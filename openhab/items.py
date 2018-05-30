# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API"""

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

import dateutil.parser
import typing

import openhab
import openhab.types

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Item:
  """Base item class"""
  types = []  # type: typing.List[typing.Type[openhab.types.CommandType]]

  def __init__(self, openhab_conn: 'openhab.client.OpenHAB', json_data: dict) -> None:
    """
    Args:
      openhab_conn (openhab.OpenHAB): openHAB object.
      json_data (dic): A dict converted from the JSON data returned by the openHAB
                       server.
    """
    self.openhab = openhab_conn
    self.type_ = None
    self.name = ''
    self._state = None  # type: typing.Optional[typing.Any]
    self.init_from_json(json_data)

  def init_from_json(self, json_data: dict):
    """Initialize this object from a json configuration as fetched from
    openHAB

    Args:
      json_data (dict): A dict converted from the JSON data returned by the openHAB
                        server.
    """
    self.name = json_data['name']
    self.type_ = json_data['type']
    self.__set_state(json_data['state'])

  @property
  def state(self) -> typing.Any:
    """The state property represents the current state of the item. The state is
    automatically refreshed from openHAB on reading it.
    Updating the value via this property send an update to the event bus.
    """
    json_data = self.openhab.get_item_raw(self.name)
    self.init_from_json(json_data)

    return self._state

  @state.setter
  def state(self, value: typing.Any):
    self.update(value)

  def _validate_value(self, value: typing.Union[str, typing.Type[openhab.types.CommandType]]):
    """Private method for verifying the new value before modifying the state of the
    item.
    """
    if self.type_ == 'String':
      if not isinstance(value, str):
        raise ValueError()
    elif len(self.types):
      for type_ in self.types:
        type_.validate(value)
    else:
      raise ValueError()

  def _parse_rest(self, value: str) -> str:
    """Parse a REST result into a native object."""
    return value

  def _rest_format(self, value: str) -> str:
    """Format a value before submitting to openHAB."""
    return value

  def __set_state(self, value: str):
    """Private method for setting the internal state."""
    if value in ('UNDEF', 'NULL'):
      self._state = None
    else:
      self._state = self._parse_rest(value)

  def __str__(self) -> str:
    return '<{0} - {1} : {2}>'.format(self.type_, self.name, self._state)

  def update(self, value: typing.Any):
    """Updates the state of an item.

    Args:
      value (object): The value to update the item with. The type of the value depends
                      on the item type and is checked accordingly.
    """
    self._validate_value(value)

    v = self._rest_format(value)

    self.openhab.req_put('/items/' + self.name + '/state', data=v)

  def command(self, value: typing.Any):
    """Sends the given value as command to the event bus.

    Args:
      value (object): The value to send as command to the event bus. The type of the
                      value depends on the item type and is checked accordingly.
    """
    self._validate_value(value)

    v = self._rest_format(value)

    self.openhab.req_post('/items/' + self.name, data=v)


class DateTimeItem(Item):
  """DateTime item type"""
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
    """Parse a REST result into a native object

    Args:
      value (str): A string argument to be converted into a datetime.datetime object.

    Returns:
      datetime.datetime: The datetime.datetime object as converted from the string
                         parameter.
    """
    return dateutil.parser.parse(value)

  def _rest_format(self, value):
    """Format a value before submitting to openHAB
    Args:
      value (datetime.datetime): A datetime.datetime argument to be converted
                                 into a string.

    Returns:
      str: The string as converted from the datetime.datetime parameter.
    """
    return value.isoformat()


class SwitchItem(Item):
  """SwitchItem item type"""
  types = [openhab.types.OnOffType]

  def on(self):
    """Set the state of the switch to ON"""
    self.command('ON')

  def off(self):
    """Set the state of the switch to OFF"""
    self.command('OFF')


class NumberItem(Item):
  """NumberItem item type"""
  types = [openhab.types.DecimalType]

  def _parse_rest(self, value):
    """Parse a REST result into a native object

    Args:
      value (str): A string argument to be converted into a float object.

    Returns:
      float: The float object as converted from the string parameter.
    """
    return float(value)

  def _rest_format(self, value):
    """Format a value before submitting to openHAB

    Args:
      value (float): A float argument to be converted into a string.

    Returns:
      str: The string as converted from the float parameter.
    """
    return str(value)


class ContactItem(Item):
  """Contact item type"""
  types = [openhab.types.OpenCloseType]

  def open(self):
    """Set the state of the contact item to OPEN"""
    self.state = 'OPEN'

  def closed(self):
    """Set the state of the contact item to CLOSED"""
    self.state = 'CLOSED'
