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

import openhab.command_types
import openhab.exceptions

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Item:
  """Base item class."""

  types: typing.Sequence[typing.Type[openhab.command_types.CommandType]] = []
  state_types: typing.Sequence[typing.Type[openhab.command_types.CommandType]] = []
  command_event_types: typing.Sequence[typing.Type[openhab.command_types.CommandType]] = []
  state_event_types: typing.Sequence[typing.Type[openhab.command_types.CommandType]] = []
  state_changed_event_types: typing.Sequence[typing.Type[openhab.command_types.CommandType]] = []

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
    self._unitOfMeasure = ''
    self._raw_state = None  # type: typing.Optional[typing.Any]  # raw state as returned by the server
    self._members = {}  # type: typing.Dict[str, typing.Any] #  group members (key = item name), for none-group items it's empty
    self.function_name: typing.Optional[str] = None
    self.function_params: typing.Optional[typing.Sequence[str]] = None

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

      if 'function' in json_data:
        self.function_name = json_data['function']['name']

        if 'params' in json_data['function']:
          self.function_params = json_data['function']['params']

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
  def unit_of_measure(self) -> str:
    """Return the unit of measure. Returns an empty string if there is none defined."""
    return self._unitOfMeasure

  @property
  def members(self) -> typing.Dict[str, typing.Any]:
    """If item is a type of Group, it will return all member items for this group.

    For none group item empty dictionary will be returned.

    Returns:
      dict: Returns a dict with item names as key and `Item` class instances as value.

    """
    return self._members

  def _validate_value(self, value: typing.Union[str, typing.Type[openhab.command_types.CommandType]]) -> None:
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
        raise ValueError(f'Invalid value "{value}"')
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

    # Only ascii encoding is supported by default. If non-ascii characters were provided, convert them to bytes.
    try:
      _ = value.encode('ascii')
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
    state = self._state
    if self._unitOfMeasure and not isinstance(self._state, tuple):
        state = f'{self._state} {self._unitOfMeasure}'
    return f'<{self.type_} - {self.name} : {state}>'

  def _update(self, value: typing.Any) -> None:
    """Updates the state of an item, input validation is expected to be already done.

    Args:
      value (object): The value to update the item with. The type of the value depends
                      on the item type and is checked accordingly.
    """
    # noinspection PyTypeChecker
    self.openhab.req_put(f'/items/{self.name}/state', data=value)

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


class GroupItem(Item):
  """String item type."""

  TYPENAME = 'Group'
  types: typing.List[typing.Type[openhab.command_types.CommandType]] = []
  state_types: typing.List[typing.Type[openhab.command_types.CommandType]] = []


class StringItem(Item):
  """String item type."""

  TYPENAME = 'String'
  types = [openhab.command_types.StringType]
  state_types = types


class DateTimeItem(Item):
  """DateTime item type."""

  TYPENAME = 'DateTime'
  types = [openhab.command_types.DateTimeType]
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
  types = [openhab.command_types.PlayPauseType, openhab.command_types.NextPrevious, openhab.command_types.RewindFastforward]
  state_types = [openhab.command_types.PlayPauseType, openhab.command_types.RewindFastforward]

  def play(self) -> None:
    """Send the command PLAY."""
    self.command(openhab.command_types.PlayPauseType.PLAY)

  def pause(self) -> None:
    """Send the command PAUSE."""
    self.command(openhab.command_types.PlayPauseType.PAUSE)

  def next(self) -> None:
    """Send the command NEXT."""
    self.command(openhab.command_types.NextPrevious.NEXT)

  def previous(self) -> None:
    """Send the command PREVIOUS."""
    self.command(openhab.command_types.NextPrevious.PREVIOUS)

  def fastforward(self) -> None:
    """Send the command FASTFORWARD."""
    self.command(openhab.command_types.RewindFastforward.FASTFORWARD)

  def rewind(self) -> None:
    """Send the command REWIND."""
    self.command(openhab.command_types.RewindFastforward.REWIND)


class SwitchItem(Item):
  """SwitchItem item type."""

  TYPENAME = 'Switch'
  types = [openhab.command_types.OnOffType]
  state_types = types

  def on(self) -> None:
    """Set the state of the switch to ON."""
    self.command(openhab.command_types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the switch to OFF."""
    self.command(openhab.command_types.OnOffType.OFF)

  def toggle(self) -> None:
    """Toggle the state of the switch to OFF to ON and vice versa."""
    if self.state == openhab.command_types.OnOffType.ON:
      self.off()
    elif self.state == openhab.command_types.OnOffType.OFF:
      self.on()


class NumberItem(Item):
  """NumberItem item type."""

  TYPENAME = 'Number'
  types = [openhab.command_types.DecimalType]
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
      m = re.match(r'(-?[0-9.]+(?:[eE]-?[0-9]+)?)\s?(.*)?$', value)

      if m:
        value = m.group(1)
        unit_of_measure = m.group(2)

        return float(value), unit_of_measure

      return float(value), ''

    except (ArithmeticError, ValueError) as exc:
      self.logger.error('Error in parsing new value "%s" for "%s" - "%s"', value, self.name, exc)

    raise ValueError(f'{self.__class__}: unable to parse value "{value}"')

  def _rest_format(self, value: typing.Union[float, typing.Tuple[float, str], str]) -> typing.Union[str, bytes]:
    """Format a value before submitting to openHAB.

    Args:
      value: Either a float, a tuple of (float, str), or string; in the first two cases we have to cast it to a string.

    Returns:
      str or bytes: A string or bytes as converted from the value parameter.
    """
    if isinstance(value, tuple) and len(value) == 2:
        return super()._rest_format(f'{value[0]:G} {value[1]}')
    if not isinstance(value, str):
        return super()._rest_format(f'{value:G}')
    return super()._rest_format(value)


class ContactItem(Item):
  """Contact item type."""

  TYPENAME = 'Contact'
  types = [openhab.command_types.OpenCloseType]
  state_types = types

  def command(self, *args: typing.Any, **kwargs: typing.Any) -> None:
    """This overrides the `Item` command method.

    Note: Commands are not accepted for items of type contact.
    """
    raise ValueError(f'This item ({self.__class__}) only supports updates, not commands!')

  def open(self) -> None:
    """Set the state of the contact item to OPEN."""
    self.state = openhab.command_types.OpenCloseType.OPEN

  def closed(self) -> None:
    """Set the state of the contact item to CLOSED."""
    self.state = openhab.command_types.OpenCloseType.CLOSED


class DimmerItem(Item):
  """DimmerItem item type."""

  TYPENAME = 'Dimmer'
  types = [openhab.command_types.OnOffType, openhab.command_types.PercentType, openhab.command_types.IncreaseDecreaseType]
  state_types = [openhab.command_types.PercentType]

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
    self.command(openhab.command_types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.command_types.OnOffType.OFF)

  def increase(self) -> None:
    """Increase the state of the dimmer."""
    self.command(openhab.command_types.IncreaseDecreaseType.INCREASE)

  def decrease(self) -> None:
    """Decrease the state of the dimmer."""
    self.command(openhab.command_types.IncreaseDecreaseType.DECREASE)


class ColorItem(DimmerItem):
  """ColorItem item type."""

  TYPENAME = 'Color'
  types = [openhab.command_types.OnOffType, openhab.command_types.PercentType, openhab.command_types.IncreaseDecreaseType, openhab.command_types.ColorType]
  state_types = [openhab.command_types.ColorType]  # type: ignore

  def _parse_rest(self, value: str) -> typing.Tuple[typing.Optional[typing.Tuple[float, float, float]], str]:  # type: ignore[override]
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a str object.

    Returns:
      HSB components
      Optional UoM
    """
    result = openhab.command_types.ColorType.parse(value)
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


class RollershutterItem(Item):
  """RollershutterItem item type."""

  TYPENAME = 'Rollershutter'
  types = [openhab.command_types.UpDownType, openhab.command_types.PercentType, openhab.command_types.StopMoveType]
  state_types = [openhab.command_types.PercentType]

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
    self.command(openhab.command_types.UpDownType.UP)

  def down(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.command_types.UpDownType.DOWN)

  def stop(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.command_types.StopMoveType.STOP)
