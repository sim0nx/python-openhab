#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals
# -*- coding: utf-8 -*-
'''python library for accessing the openHAB REST API'''

#
# Georges Toth (c) 2016 <georges@trypill.org>
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
import dateutil.parser

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Item(object):
  '''Base item class'''
  def __init__(self, openhab, json_data):
    self.openhab = openhab
    self.type_ = None
    self.name = ''
    self._state = None
    self.init_from_json(json_data)

  def init_from_json(self, json_data):
    '''Initialize this object from a json configuration as fetched from
    openHAB'''
    self.name = json_data['name']
    self.type_ = json_data['type']
    self.__set_state(json_data['state'])

  @property
  def state(self):
    '''Update internal state and return it'''
    json_data = self.openhab.get_item_raw(self.name)
    self.init_from_json(json_data)

    return self._state

  @state.setter
  def state(self, value):
    '''Updates the state of an item'''
    self.update(value)

  def _validate_value(self, value):
    if self.type_ == 'String':
      if not (isinstance(value, str) or isinstance(value, unicode)):
        raise ValueError()
    else:
      raise ValueError()

  def _parse_rest(self, value):
    '''Parse a REST result into a native object'''
    return value

  def _rest_format(self, value):
    '''Format a value before submitting to openHAB'''
    return value

  def __set_state(self, value):
    '''Private method for setting the internal state'''
    if value in ('UNDEF', 'NULL'):
      self._state = None
    else:
      self._state = self._parse_rest(value)

  def __str__(self):
    return u'<{0} - {1} : {2}>'.format(self.type_, self.name,
                                       self._state).encode('utf-8')

  def update(self, value):
    self._validate_value(value)

    v = self._rest_format(value)

    self.openhab.req_put('/items/' + self.name + '/state', data=v)

  def command(self, value):
    '''Sends a command to an item'''
    self._validate_value(value)

    v = self._rest_format(value)

    self.openhab.req_post('/items/' + self.name, data=v)


class DateTimeItem(Item):
  '''DateTime item type'''
  def __gt__(self, other):
    return self._state > other

  def __lt__(self, other):
    return not self.__gt__(other)

  def __eq__(self, other):
    return self._state == other

  def __ne__(self, other):
    return not self.__eq__(other)

  @Item.state.setter
  def state(self, value):
    if not isinstance(value, datetime.datetime):
      raise ValueError()

    Item.state.fset(self, value)

  def _parse_rest(self, value):
    '''Parse a REST result into a native object'''
    return dateutil.parser.parse(value)

  def _rest_format(self, value):
    '''Format a value before submitting to openHAB'''
    return value.strftime('%Y-%m-%d %H:%M:%S')

  def _validate_value(self, value):
    if not isinstance(value, datetime.datetime):
      raise ValueError()


class SwitchItem(Item):
  '''Switch item type'''
  @Item.state.setter
  def state(self, value):
    if value not in ['ON', 'OFF']:
      raise ValueError()

    Item.state.fset(self, value)

  def on(self):
    '''Set the state of the switch to ON'''
    self.state = 'ON'

  def off(self):
    '''Set the state of the switch to OFF'''
    self.state = 'OFF'

  def _validate_value(self, value):
    if not (isinstance(value, str) or isinstance(value, unicode)) or\
       value not in ['ON', 'OFF']:
      raise ValueError()


class NumberItem(Item):
  '''Number item type'''
  @Item.state.setter
  def state(self, value):
    if not (isinstance(value, float) or isinstance(value, int)):
      raise ValueError()

    Item.state.fset(self, value)

  def _parse_rest(self, value):
    '''Parse a REST result into a native object'''
    return float(value)

  def _rest_format(self, value):
    '''Format a value before submitting to openHAB'''
    return str(value)

  def _validate_value(self, value):
    if not (isinstance(value, float) or isinstance(value, int)):
      raise ValueError()


class ContactItem(Item):
  '''Contact item type'''
  @Item.state.setter
  def state(self, value):
    if value not in ['OPEN', 'CLOSED']:
      raise ValueError()

    Item.state.fset(self, value)

  def open(self):
    '''Set the state of the switch to OPEN'''
    self.state = 'OPEN'

  def closed(self):
    '''Set the state of the switch to CLOSED'''
    self.state = 'CLOSED'

  def _validate_value(self, value):
    if not (isinstance(value, str) or isinstance(value, unicode)) or\
       value not in ['OPEN', 'CLOSED']:
      raise ValueError()
