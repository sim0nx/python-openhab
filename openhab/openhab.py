#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Georges Toth (c) 2014 <georges@trypill.org>
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

import datetime
import json
import requests
import dateutil.parser


# fetch all items
def fetch_all_items(base_url, autoupdate=False):
  items = {}
  r = requests.get(base_url + '/items/', headers={'accept': 'application/json'}).json()

  for i in r['item']:
    # we ignore group-items for now
    if i['type'] == 'GroupItem':
      continue
  
    if not i['name'] in items:
      e = init_from_json(base_url, i, autoupdate=autoupdate)
      items[i['name']] = e

  return items


def fetch_item_json(base_url, name):
  r = requests.get(base_url + '/items/' + name, headers={'accept': 'application/json'})

  if r.status_code == requests.codes.ok:
    return r.json()
  else:
    r.raise_for_status()


def init_from_json(base_url, j, **kwargs):
  name = j['name']
  type_ = j['type']
  state = j['state']
  class_ = get_class(type_)

  i = class_(name, string_state=state, autoupdate=kwargs.get('autoupdate', False))
  i.base_url = base_url

  if i.__class__ == Item:
    i._type = type_

  return i


def get_item(base_url, name, **kwargs):
  j = fetch_item_json(base_url, name)

  return init_from_json(base_url, j, **kwargs)


def get_class(type_):
  if type_ == 'SwitchItem':
    return SwitchItem
  elif type_ == 'DateTimeItem':
    return DateTimeItem
  elif type_ == 'NumberItem':
    return NumberItem

  return Item


class BaseItem(object):
  def __init__(self, name, type_=None, string_state=None, autoupdate=False):
    self.name = name
    self.lastupdate = None
    self._type = None
    self._autoupdate = autoupdate

    if not string_state is None:
      self.update_from_string(string_state)
    else:
      self.state = None

    if not type_ is None:
      self._type = type_

  def update_from_string(self, value):
    if not (isinstance(value, str) or isinstance(value, unicode)):
      raise ValueError()

    if value in ('Uninitialized', 'Undefined'):
      self._set_state(None)

      return True

    self._set_state(value)

    return False

  def _set_state(self, value):
    self._state = value
    self.lastupdate = datetime.datetime.now()

  def to_openhab(self):
    if self.state is None:
      return 'Undefined'

    return str(self.state)

  @property
  def state(self):
    return self._state

  @state.setter
  def state(self, value):
    if value is None or isinstance(value, str) or isinstance(value, unicode):
      self._state = value
    else:
      raise ValueError()

    if self._autoupdate:
      self.post_state()

  def fetch_state(self):
    j = fetch_item_json(self.base_url, self.name)

    self.update_from_string(j['state'])

    return self.state

  def post_state(self):
    r = requests.post(self.base_url + '/items/' + self.name, data=self.to_openhab(), headers={'accept': 'application/json'})

    if r.status_code == requests.codes.ok:
      return r.json()
    else:
      r.raise_for_status()

  def __str__(self):
    return u'<{0} - {1} : {2}>'.format(self._type, self.name, self._state).encode('utf-8')


class Item(BaseItem):
  def __init__(self, name, **kwargs):
    super(Item, self).__init__(name, type_='Item', **kwargs)

  @BaseItem.state.setter
  def state(self, value):
    if value is None or isinstance(value, str) or isinstance(value, unicode):
      self._state = value
    else:
      raise ValueError()

    if self._autoupdate:
      self.post_state()

  def update_from_string(self, value):
    if not super(Item, self).update_from_string(value):
      self._set_state(value)

  def to_openhab(self):
    if self.state is None:
      return 'Undefined'

    return self.state


class DateTimeItem(BaseItem):
  def __init__(self, name, **kwargs):
    super(DateTimeItem, self).__init__(name, type_='DateTimeItem', **kwargs)

  def __gt__(self, other):
    return self.state > other

  def __lt__(self, other):
    return not self.__gt__(other)

  def __eq__(self, other):
    return self.state == other

  def __ne__(self, other):
    return not self.__eq__(other)

  @BaseItem.state.setter
  def state(self, value):
    if value is None or isinstance(value, datetime.datetime):
      self._set_state(value)
    else:
      raise ValueError()

    if self._autoupdate:
      self.post_state()

  def update_from_string(self, value):
    if not super(DateTimeItem, self).update_from_string(value):
      self._set_state(dateutil.parser.parse(value))

  def to_openhab(self):
    if self.state is None:
      return 'Undefined'

    return self.state.strftime('%Y-%m-%d %H:%M:%S')


class SwitchItem(BaseItem):
  def __init__(self, name, **kwargs):
    super(SwitchItem, self).__init__(name, type_='SwitchItem', **kwargs)

  @BaseItem.state.setter
  def state(self, value):
    if value is None:
      self._set_state(None)
    elif isinstance(value, bool):
      self._set_state(bool(value))
    else:
      raise ValueError()

    if self._autoupdate:
      self.post_state()

  def on(self):
    self.state = True

  def off(self):
    self.state = False

  def update_from_string(self, value):
    if not super(SwitchItem, self).update_from_string(value):
      if value == 'ON':
        self._set_state(True)
      elif value == 'OFF':
        self._set_state(False)
      else:
        raise ValueError()

  def to_openhab(self):
    if self.state is None:
      return 'Undefined'
    elif self.state == True:
      return 'ON'
 
    return 'OFF' 


class NumberItem(BaseItem):
  def __init__(self, name, **kwargs):
    super(NumberItem, self).__init__(name, type_='NumberItem', **kwargs)

  @BaseItem.state.setter
  def state(self, value):
    if value is None:
      self._set_state(None)
    elif isinstance(value, float) or isinstance(value, int):
      self._set_state(value)
    else:
      raise ValueError()

    if self._autoupdate:
      self.post_state()

  def update_from_string(self, value):
    if not super(NumberItem, self).update_from_string(value):
      if '.' in value:
        self._set_state(float(value))
      else:
        self._set_state(int(value))
