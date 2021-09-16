# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API."""

#
# Georges Toth (c) 2016-present <georges@trypill.org>
#
# python-openhab is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-openhab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-openhab.  If not, see <http://www.gnu.org/licenses/>.
#

# pylint: disable=bad-indentation

import datetime
import logging
import re
import typing

import dateutil.parser

import openhab.exceptions
import openhab.types

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Item:
  """Base item class."""

  types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  command_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_changed_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []

  TYPENAME = 'unknown'

  def __init__(self, openhab_conn: 'openhab.client.OpenHAB', json_data: dict) -> None:
    """Constructor.

    Args:
      openhab_conn (openhab.OpenHAB): openHAB object.
      json_data (dic): A dict converted from the JSON data returned by the openHAB
                       server.
    """
    self.openhab = openhab_conn
    self.type_: typing.Optional[str] = None
    self.quantityType: typing.Optional[str] = None
    self.editable = None
    self.label = ''
    self.category = ''
    self.tags = ''
    self.groupNames = ''
    self.group = False
    self.name = ''
    self._state = None  # type: typing.Optional[typing.Any]
    self._raw_state = None  # type: typing.Optional[typing.Any]  # raw state as returned by the server
    self._members = {}  # type: typing.Dict[str, typing.Any] #  group members (key = item name), for none-group items it's empty

    self.logger = logging.getLogger(__name__)

    self.init_from_json(json_data)

  def init_from_json(self, json_data: dict) -> None:
    """Initialize this object from a json configuration as fetched from openHAB.

    Args:
      json_data (dict): A dict converted from the JSON data returned by the openHAB
                        server.
    """
    self.name = json_data['name']
    if json_data['type'] == 'Group':
      self.group = True
      if 'groupType' in json_data:
        self.type_ = json_data['groupType']

      # init members
      for i in json_data['members']:
        self.members[i['name']] = self.openhab.json_to_item(i)

    else:
      self.type_ = json_data.get('type', None)

      if self.type_ is None:
        raise openhab.exceptions.InvalidReturnException('Item did not return a type attribute.')

      parts = self.type_.split(':')
      if len(parts) == 2:
        self.quantityType = parts[1]

    if 'editable' in json_data:
      self.editable = json_data['editable']
    if 'label' in json_data:
      self.label = json_data['label']
    if 'category' in json_data:
      self.category = json_data['category']
    if 'tags' in json_data:
      self.tags = json_data['tags']
    if 'groupNames' in json_data:
      self.groupNames = json_data['groupNames']

    self._raw_state = json_data['state']

    if self.is_undefined(self._raw_state):
      self._state = None
    else:
      self._state, self._unitOfMeasure = self._parse_rest(self._raw_state)

  @property
  def state(self) -> typing.Any:
    """The state property represents the current state of the item.

    The state is automatically refreshed from openHAB on reading it.
    Updating the value via this property send an update to the event bus.
    """
    json_data = self.openhab.get_item_raw(self.name)
    self.init_from_json(json_data)

    return self._state

  @state.setter
  def state(self, value: typing.Any) -> None:
    self.update(value)

  @property
  def members(self) -> typing.Dict[str, typing.Any]:
    """If item is a type of Group, it will return all member items for this group.

    For none group item empty dictionary will be returned.

    Returns:
      dict: Returns a dict with item names as key and `Item` class instances as value.

    """
    return self._members

  def _validate_value(self, value: typing.Union[str, typing.Type[openhab.types.CommandType]]) -> None:
    """Private method for verifying the new value before modifying the state of the item."""
    if self.type_ == 'String':
      if not isinstance(value, (str, bytes)):
        raise ValueError()
    elif self.types:
      validation = False

      for type_ in self.types:
        try:
          type_.validate(value)
        except ValueError:
          pass
        else:
          validation = True

      if not validation:
        raise ValueError('Invalid value "{}"'.format(value))
    else:
      raise ValueError()

  def _parse_rest(self, value: str) -> typing.Tuple[str, str]:
    """Parse a REST result into a native object."""
    # pylint: disable=no-self-use
    return value, ''

  def _rest_format(self, value: str) -> typing.Union[str, bytes]:
    """Format a value before submitting to openHAB."""
    # pylint: disable=no-self-use
    _value = value  # type: typing.Union[str, bytes]

    # Only latin-1 encoding is supported by default. If non-latin-1 characters were provided, convert them to bytes.
    try:
      _ = value.encode('latin-1')
    except UnicodeError:
      _value = value.encode('utf-8')

    return _value

  def is_undefined(self, value: str) -> bool:
    """Check if value is undefined."""
    for aStateType in self.state_types:
      if not aStateType.is_undefined(value):
        return False

    return True

  def __str__(self) -> str:
    """String representation."""
    return '<{0} - {1} : {2}>'.format(self.type_, self.name, self._state)

  def _update(self, value: typing.Any) -> None:
    """Updates the state of an item, input validation is expected to be already done.

    Args:
      value (object): The value to update the item with. The type of the value depends
                      on the item type and is checked accordingly.
    """
    # noinspection PyTypeChecker
    self.openhab.req_put('/items/{}/state'.format(self.name), data=value)

  def update(self, value: typing.Any) -> None:
    """Updates the state of an item.

    Args:
      value (object): The value to update the item with. The type of the value depends
                      on the item type and is checked accordingly.
    """
    self._validate_value(value)

    v = self._rest_format(value)

    self._state = value

    self._update(v)

  def command(self, value: typing.Any) -> None:
    """Sends the given value as command to the event bus.

    Args:
      value (object): The value to send as command to the event bus. The type of the
                      value depends on the item type and is checked accordingly.
    """
    self._validate_value(value)

    v = self._rest_format(value)

    self._state = value

    self.openhab.req_post(f'/items/{self.name}', data=v)

  def update_state_null(self) -> None:
    """Update the state of the item to *NULL*."""
    self._update('NULL')

  def update_state_undef(self) -> None:
    """Update the state of the item to *UNDEF*."""
    self._update('UNDEF')

  def is_state_null(self) -> bool:
    """If the item state is None, use this method for checking if the remote value is NULL."""
    if self.state is None:
      # we need to query the current remote state as else this method will not work correctly if called after
      # either update_state method
      if self._raw_state is None:
        # This should never happen
        raise ValueError('Invalid internal (raw) state.')

      return self._raw_state == 'NULL'

    return False

  def is_state_undef(self) -> bool:
    """If the item state is None, use this method for checking if the remote value is UNDEF."""
    if self.state is None:
      # we need to query the current remote state as else this method will not work correctly if called after
      # either update_state method
      if self._raw_state is None:
        # This should never happen
        raise ValueError('Invalid internal (raw) state.')

      return self._raw_state == 'UNDEF'

    return False

  def create_or_update_item(self,
                            name: str,
                            _type: typing.Union[str, typing.Type['Item']],
                            quantity_type: typing.Optional[str] = None,
                            label: typing.Optional[str] = None,
                            category: typing.Optional[str] = None,
                            tags: typing.Optional[typing.List[str]] = None,
                            group_names: typing.Optional[typing.List[str]] = None,
                            group_type: typing.Optional[str] = None,
                            function_name: typing.Optional[str] = None,
                            function_params: typing.Optional[typing.List[str]] = None
                            ) -> None:
    """Creates a new item in openHAB if there is no item with name 'name' yet.

    If there is an item with 'name' already in openHAB, the item gets updated with the infos provided. be aware that not provided fields will be deleted in openHAB.
    Consider to get the existing item via 'getItem' and then read out existing fields to populate the parameters here.

    Args:
      name: unique name of the item
      _type: the data_type used in openHAB (like Group, Number, Contact, DateTime, Rollershutter, Color, Dimmer, Switch, Player)
                       server.
                       To create groups use the itemtype 'Group'!
      quantity_type: optional quantity_type ( like Angle, Temperature, Illuminance (see https://www.openhab.org/docs/concepts/units-of-measurement.html))
      label: optional openHAB label (see https://www.openhab.org/docs/configuration/items.html#label)
      category: optional category. no documentation found
      tags: optional list of tags (see https://www.openhab.org/docs/configuration/items.html#tags)
      group_names: optional list of groups this item belongs to.
      group_type: optional group_type. no documentation found
      function_name: optional function_name. no documentation found
      function_params: optional list of function Params. no documentation found
    """
    paramdict: typing.Dict[str, typing.Union[str, typing.List[str], typing.Dict[str, typing.Union[str, typing.List]]]] = {}

    if isinstance(_type, type):
      if issubclass(_type, Item):
        itemtypename = _type.TYPENAME
      else:
        raise ValueError(f'_type parameter must be a valid subclass of type *Item* or a string name of such a class; given value is "{str(_type)}"')
    else:
      itemtypename = _type

    if quantity_type is None:
      paramdict['type'] = itemtypename
    else:
      paramdict['type'] = f'{itemtypename}:{quantity_type}'

    paramdict['name'] = name

    if label is not None:
      paramdict['label'] = label

    if category is not None:
      paramdict['category'] = category

    if tags is not None:
      paramdict['tags'] = tags

    if group_names is not None:
      paramdict['groupNames'] = group_names

    if group_type is not None:
      paramdict['groupType'] = group_type

    if function_name is not None and function_params is not None:
      paramdict['function'] = {'name': function_name, 'params': function_params}

    self.logger.debug('About to create item with PUT request:\n%s', str(paramdict))
    self.openhab.req_put(f'/items/{name}', data=paramdict)


class StringItem(Item):
  """String item type."""

  TYPENAME = 'String'
  types = [openhab.types.StringType]
  state_types = types


class DateTimeItem(Item):
  """DateTime item type."""

  TYPENAME = 'DateTime'
  types = [openhab.types.DateTimeType]
  state_types = types

  def __gt__(self, other: datetime.datetime) -> bool:
    """Greater than comparison."""
    if self._state is None or not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state > other

  def __ge__(self, other: datetime.datetime) -> bool:
    """Greater or equal comparison."""
    if self._state is None or not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state >= other

  def __lt__(self, other: object) -> bool:
    """Less than comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return not self.__gt__(other)

  def __le__(self, other: object) -> bool:
    """Less or equal comparison."""
    if self._state is None or not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state <= other

  def __eq__(self, other: object) -> bool:
    """Equality comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state == other

  def __ne__(self, other: object) -> bool:
    """Not equal comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return not self.__eq__(other)

  def _parse_rest(self, value: str) -> typing.Tuple[datetime.datetime, str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a datetime.datetime object.

    Returns:
      datetime.datetime: The datetime.datetime object as converted from the string
                         parameter.
    """
    return dateutil.parser.parse(value), ''

  def _rest_format(self, value: datetime.datetime) -> str:  # type: ignore[override]
    """Format a value before submitting to openHAB.

    Args:
      value (datetime.datetime): A datetime.datetime argument to be converted
                                 into a string.

    Returns:
      str: The string as converted from the datetime.datetime parameter.
    """
    # openHAB supports only up to milliseconds as of this writing
    return value.isoformat(timespec='milliseconds')


class PlayerItem(Item):
  """PlayerItem item type."""

  TYPENAME = 'Player'
  types = [openhab.types.PlayPauseType, openhab.types.NextPrevious, openhab.types.RewindFastforward]
  state_types = [openhab.types.PlayPauseType, openhab.types.RewindFastforward]

  def play(self) -> None:
    """Send the command PLAY."""
    self.command(openhab.types.PlayPauseType.PLAY)

  def pause(self) -> None:
    """Send the command PAUSE."""
    self.command(openhab.types.PlayPauseType.PAUSE)

  def next(self) -> None:
    """Send the command NEXT."""
    self.command(openhab.types.NextPrevious.NEXT)

  def previous(self) -> None:
    """Send the command PREVIOUS."""
    self.command(openhab.types.NextPrevious.PREVIOUS)

  def fastforward(self) -> None:
    """Send the command FASTFORWARD."""
    self.command(openhab.types.RewindFastforward.FASTFORWARD)

  def rewind(self) -> None:
    """Send the command REWIND."""
    self.command(openhab.types.RewindFastforward.REWIND)


class SwitchItem(Item):
  """SwitchItem item type."""

  TYPENAME = 'Switch'
  types = [openhab.types.OnOffType]
  state_types = types

  def on(self) -> None:
    """Set the state of the switch to ON."""
    self.command(openhab.types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the switch to OFF."""
    self.command(openhab.types.OnOffType.OFF)

  def toggle(self) -> None:
    """Toggle the state of the switch to OFF to ON and vice versa."""
    if self.state == openhab.types.OnOffType.ON:
      self.off()
    elif self.state == openhab.types.OnOffType.OFF:
      self.on()


class NumberItem(Item):
  """NumberItem item type."""

  TYPENAME = 'Number'
  types = [openhab.types.DecimalType]
  state_types = types

  def _parse_rest(self, value: str) -> typing.Tuple[typing.Union[float, None], str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a float object.

    Returns:
      float: The float object as converted from the string parameter.
      str: The unit Of Measure or empty string
    """
    if value in ('UNDEF', 'NULL'):
      return None, ''
    # m = re.match(r'''^(-?[0-9.]+)''', value)
    try:
      m = re.match(r'(-?[0-9.]+)\s?(.*)?$', value)

      if m:
        value = m.group(1)
        unit_of_measure = m.group(2)

        return float(value), unit_of_measure

      return float(value), ''

    except (ArithmeticError, ValueError) as exc:
      self.logger.error('error in parsing new value "{}" for "{}"'.format(value, self.name), exc)

    raise ValueError('{}: unable to parse value "{}"'.format(self.__class__, value))

  def _rest_format(self, value: float) -> str:  # type: ignore[override]
    """Format a value before submitting to openHAB.

    Args:
      value (float): A float argument to be converted into a string.

    Returns:
      str: The string as converted from the float parameter.
    """
    return str(value)


class ContactItem(Item):
  """Contact item type."""

  TYPENAME = 'Contact'
  types = [openhab.types.OpenCloseType]
  state_types = types

  def command(self, *args: typing.Any, **kwargs: typing.Any) -> None:
    """This overrides the `Item` command method.

    Note: Commands are not accepted for items of type contact.
    """
    raise ValueError('This item ({}) only supports updates, not commands!'.format(self.__class__))

  def open(self) -> None:
    """Set the state of the contact item to OPEN."""
    self.state = openhab.types.OpenCloseType.OPEN

  def closed(self) -> None:
    """Set the state of the contact item to CLOSED."""
    self.state = openhab.types.OpenCloseType.CLOSED


class DimmerItem(Item):
  """DimmerItem item type."""

  TYPENAME = 'Dimmer'
  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType]
  state_types = [openhab.types.PercentType]

  def _parse_rest(self, value: str) -> typing.Tuple[float, str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      float: The int object as converted from the string parameter.
      str: Possible UoM
    """
    return float(value), ''

  def _rest_format(self, value: typing.Union[str, int]) -> str:
    """Format a value before submitting to OpenHAB.

    Args:
      value: Either a string or an integer; in the latter case we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if not isinstance(value, str):
      return str(value)

    return value

  def on(self) -> None:
    """Set the state of the dimmer to ON."""
    self.command(openhab.types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.OnOffType.OFF)

  def increase(self) -> None:
    """Increase the state of the dimmer."""
    self.command(openhab.types.IncreaseDecreaseType.INCREASE)

  def decrease(self) -> None:
    """Decrease the state of the dimmer."""
    self.command(openhab.types.IncreaseDecreaseType.DECREASE)


class ColorItem(DimmerItem):
  """ColorItem item type."""

  TYPENAME = 'Color'
  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType, openhab.types.ColorType]
  state_types = [openhab.types.ColorType]  # type: ignore

  def _parse_rest(self, value: str) -> typing.Tuple[typing.Optional[typing.Tuple[int, int, float]], str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a str object.

    Returns:
      HSB components
      Optional UoM
    """
    result = openhab.types.ColorType.parse(value)
    return result, ''

  def _rest_format(self, value: typing.Union[typing.Tuple[int, int, float], str, int]) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value: Either a string, an integer or a tuple of HSB components (int, int, float); in the latter two cases we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if isinstance(value, tuple):
      if len(value) == 3:
        return f'{value[0]},{value[1]},{value[2]}'

    if not isinstance(value, str):
      return str(value)

    return value

  @staticmethod
  def __extract_value_and_unitofmeasure(value: str) -> typing.Tuple[str, str]:
    return value, ''


class RollershutterItem(Item):
  """RollershutterItem item type."""

  TYPENAME = 'Rollershutter'
  types = [openhab.types.UpDownType, openhab.types.PercentType, openhab.types.StopMoveType]
  state_types = [openhab.types.PercentType]

  def _parse_rest(self, value: str) -> typing.Tuple[int, str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      int: The int object as converted from the string parameter.
      str: Possible UoM
    """
    return int(float(value)), ''

  def _rest_format(self, value: typing.Union[str, int]) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value: Either a string or an integer; in the latter case we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if not isinstance(value, str):
      return str(value)

    return value

  def up(self) -> None:
    """Set the state of the dimmer to ON."""
    self.command(openhab.types.UpDownType.UP)

  def down(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.UpDownType.DOWN)

  def stop(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.StopMoveType.STOP)
