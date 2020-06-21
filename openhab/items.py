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

import logging
import re
import typing

import dateutil.parser

import openhab.types

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Item:
  """Base item class."""

  types = []  # type: typing.List[typing.Type[openhab.types.CommandType]]

  def __init__(self, openhab_conn: 'openhab.client.OpenHAB', json_data: dict) -> None:
    """Constructor.

    Args:
      openhab_conn (openhab.OpenHAB): openHAB object.
      json_data (dic): A dict converted from the JSON data returned by the openHAB
                       server.
    """
    self.openhab = openhab_conn
    self.type_ = None
    self.group = False
    self.name = ''
    self._state = None  # type: typing.Optional[typing.Any]
    self._raw_state = None  # type: typing.Optional[typing.Any]  # raw state as returned by the server
    self._members = {}  # type: typing.Dict[str, typing.Any] #  group members (key = item name), for none-group items it's empty

    self.logger = logging.getLogger(__name__)

    self.init_from_json(json_data)

  def init_from_json(self, json_data: dict):
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
      self.type_ = json_data['type']
    self.__set_state(json_data['state'])

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
  def state(self, value: typing.Any):
    self.update(value)

  @property
  def members(self):
    """If item is a type of Group, it will return all member items for this group.

    For none group item empty dictionary will be returned.

    Returns:
      dict: Returns a dict with item names as key and `Item` class instances as value.

    """
    return self._members

  def _validate_value(self, value: typing.Union[str, typing.Type[openhab.types.CommandType]]):
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

  def _parse_rest(self, value: str) -> str:
    """Parse a REST result into a native object."""
    return value

  def _rest_format(self, value: str) -> typing.Union[str, bytes]:
    """Format a value before submitting to openHAB."""
    _value = value  # type: typing.Union[str, bytes]

    # Only latin-1 encoding is supported by default. If non-latin-1 characters were provided, convert them to bytes.
    try:
      _ = value.encode('latin-1')
    except UnicodeError:
      _value = value.encode('utf-8')

    return _value

  def __set_state(self, value: str) -> None:
    """Private method for setting the internal state."""
    self._raw_state = value

    if value in ('UNDEF', 'NULL'):
      self._state = None
    else:
      self._state = self._parse_rest(value)

  def __str__(self) -> str:
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

    self._update(v)

  # noinspection PyTypeChecker
  def command(self, value: typing.Any) -> None:
    """Sends the given value as command to the event bus.

    Args:
      value (object): The value to send as command to the event bus. The type of the
                      value depends on the item type and is checked accordingly.
    """
    self._validate_value(value)

    v = self._rest_format(value)

    self.openhab.req_post('/items/{}'.format(self.name), data=v)

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


class DateTimeItem(Item):
  """DateTime item type."""

  types = [openhab.types.DateTimeType]

  def __gt__(self, other):
    return self._state > other

  def __lt__(self, other):
    return not self.__gt__(other)

  def __eq__(self, other):
    return self._state == other

  def __ne__(self, other):
    return not self.__eq__(other)

  def _parse_rest(self, value):
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a datetime.datetime object.

    Returns:
      datetime.datetime: The datetime.datetime object as converted from the string
                         parameter.
    """
    return dateutil.parser.parse(value)

  def _rest_format(self, value):
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

  types = [openhab.types.PlayerType]

  def play(self) -> None:
    """Set the state of the player to PLAY."""
    self.command('PLAY')

  def pause(self) -> None:
    """Set the state of the player to PAUSE."""
    self.command('PAUSE')

  def next(self) -> None:
    """Set the state of the player to NEXT."""
    self.command('NEXT')

  def previous(self) -> None:
    """Set the state of the player to PREVIOUS."""
    self.command('PREVIOUS')


class SwitchItem(Item):
  """SwitchItem item type."""

  types = [openhab.types.OnOffType]

  def on(self) -> None:
    """Set the state of the switch to ON."""
    self.command('ON')

  def off(self) -> None:
    """Set the state of the switch to OFF."""
    self.command('OFF')

  def toggle(self) -> None:
    """Toggle the state of the switch to OFF to ON and vice versa."""
    if self.state == 'ON':
      self.off()
    else:
      self.on()


class NumberItem(Item):
  """NumberItem item type."""

  types = [openhab.types.DecimalType]

  def _parse_rest(self, value: str) -> float:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a float object.

    Returns:
      float: The float object as converted from the string parameter.
    """
    # Items of type NumberItem may contain units of measurement. Here we make sure to strip them off.
    # @TODO possibly implement supporting UoM data for NumberItems not sure this would be useful.
    m = re.match(r'''^(-?[0-9.]+)''', value)

    if m:
      return float(m.group(1))

    raise ValueError('{}: unable to parse value "{}"'.format(self.__class__, value))

  def _rest_format(self, value: float) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value (float): A float argument to be converted into a string.

    Returns:
      str: The string as converted from the float parameter.
    """
    return str(value)


class ContactItem(Item):
  """Contact item type."""

  types = [openhab.types.OpenCloseType]

  def command(self, *args, **kwargs) -> None:
    """This overrides the `Item` command method.

    Note: Commands are not accepted for items of type contact.
    """
    raise ValueError('This item ({}) only supports updates, not commands!'.format(self.__class__))

  def open(self) -> None:
    """Set the state of the contact item to OPEN."""
    self.state = 'OPEN'

  def closed(self) -> None:
    """Set the state of the contact item to CLOSED."""
    self.state = 'CLOSED'


class DimmerItem(Item):
  """DimmerItem item type."""

  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType]

  def _parse_rest(self, value: str) -> int:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      int: The int object as converted from the string parameter.
    """
    return int(float(value))

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
    self.command('ON')

  def off(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command('OFF')

  def increase(self) -> None:
    """Increase the state of the dimmer."""
    self.command('INCREASE')

  def decrease(self) -> None:
    """Decrease the state of the dimmer."""
    self.command('DECREASE')


class ColorItem(Item):
  """ColorItem item type."""

  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType,
           openhab.types.ColorType]

  def _parse_rest(self, value: str) -> str:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a str object.

    Returns:
      str: The str object as converted from the string parameter.
    """
    return str(value)

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

  def on(self) -> None:
    """Set the state of the color to ON."""
    self.command('ON')

  def off(self) -> None:
    """Set the state of the color to OFF."""
    self.command('OFF')

  def increase(self) -> None:
    """Increase the state of the color."""
    self.command('INCREASE')

  def decrease(self) -> None:
    """Decrease the state of the color."""
    self.command('DECREASE')


class RollershutterItem(Item):
  """RollershutterItem item type."""

  types = [openhab.types.UpDownType, openhab.types.PercentType, openhab.types.StopType]

  def _parse_rest(self, value: str) -> int:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      int: The int object as converted from the string parameter.
    """
    return int(float(value))

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
    self.command('UP')

  def down(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command('DOWN')

  def stop(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command('STOP')
