#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Georges Toth (c) 2014 <georges@trypill.org>
#
# eml_parser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# eml_parser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with eml_parser.  If not, see <http://www.gnu.org/licenses/>.
#

import datetime
import json
import requests
import dateutil.parser


class Item(object):
  def __init__(self, name):
    self.name = name
    self.type_ = ''
    self.state_ = ''

  def init_from_json(self, j):
    self.name = j['name']
    self.type_ = j['type']
    self.__set_state(j['state'])

  @staticmethod
  def initj(base_url, j):
    if j['type'] == 'SwitchItem':
      i = SwitchItem(j)
    elif j['type'] == 'DateTimeItem':
      i = DateTimeItem(j)
    elif j['type'] == 'NumberItem':
      i = NumberItem(j)
    else:
      i = Item(j['name'])
      i.init_from_json(j)

    i.base_url = base_url

    return i

  @staticmethod
  def init(base_url, name):
    j = Item.__get_item(base_url, name)

    if j['type'] == 'SwitchItem':
      i = SwitchItem(j)
    elif j['type'] == 'DateTimeItem':
      i = DateTimeItem(j)
    else:
      i = Item(name)
      i.state

    i.base_url = base_url

    return i

  @property
  def state(self):
    j = Item.__get_item(self.base_url, self.name)

    self.type_ = j['type']
    self.__set_state(j['state'])

    return self.state_

  @state.setter
  def state(self, value):
    v = value

    if self.type_ == 'DateTimeItem':
      if not isinstance(v, datetime.datetime):
        raise ValueError()
      else:
        v = value.strftime('%Y-%m-%d %H:%M:%S')
    elif self.type_ == 'NumberItem':
      if not (isinstance(value, float) or isinstance(value, int)):
        raise ValueError()
      else:
        v = str(v)
    elif self.type_ == 'SwitchItem':
      if not (isinstance(value, str) or isinstance(value, unicode)) or not value in ['ON', 'OFF']:
        raise ValueError()
    else:
      raise ValueError()

    r = requests.post(self.base_url + '/items/' + self.name, data=v, headers={'accept': 'application/json'})

    if r.status_code == requests.codes.ok:
      return r.json()
    else:
      r.raise_for_status()

  @staticmethod
  def __get_item(base_url, name):
    r = requests.get(base_url + '/items/' + name, headers={'accept': 'application/json'})

    if r.status_code == requests.codes.ok:
      return r.json()
    else:
      r.raise_for_status()

  def __set_state(self, value):
    if self.type_ == 'DateTimeItem':
      self.state_ = dateutil.parser.parse(value)
    elif self.type_ == 'NumberItem':
      if value in ('Uninitialized', 'Undefined'):
        self.state_ = None
      else:
        self.state_ = float(value)
    else:
      self.state_ = value


class DateTimeItem(Item):
  def __init__(self, j):
    super(DateTimeItem, self).init_from_json(j)

  def __gt__(self, other):
    return self.state_ > other

  def __lt__(self, other):
    return not self.__gt__(other)

  def __eq__(self, other):
    return self.state_ == other

  def __ne__(self, other):
    return not self.__eq__(other)

  @Item.state.setter
  def state(self, value):
    if not isinstance(value, datetime.datetime):
      raise ValueError()

    Item.state.fset(self, value)


class SwitchItem(Item):
  def __init__(self, j):
    super(SwitchItem, self).init_from_json(j)

  @Item.state.setter
  def state(self, value):
    if not value in ['ON', 'OFF']:
      raise ValueError()

    Item.state.fset(self, value)

  def on(self):
    self.state = 'ON'

  def off(self):
    self.state = 'OFF'


class NumberItem(Item):
  def __init__(self, j):
    super(NumberItem, self).init_from_json(j)

  @Item.state.setter
  def state(self, value):
    if not (isinstance(value, float) or isinstance(value, int)):
      raise ValueError()

    Item.state.fset(self, value)
