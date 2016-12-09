#!/usr/bin/env python
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

import requests
from items import *

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'



class openHAB(object):
  def __init__(self, base_url):
    self.base_url = base_url

    self.session = requests.Session()
    self.session.headers['accept'] = 'application/json'

  def _check_req_return(self, req):
    if not (req.status_code >= 200 and req.status_code < 300):
      req.raise_for_status()

  def req_get(self, uri_path):
    r = self.session.get(self.base_url + uri_path)
    self._check_req_return(r)
    return r.json()

  def req_post(self, uri_path, data=None):
    r = self.session.post(self.base_url + uri_path, data=data)
    self._check_req_return(r)

  def req_put(self, uri_path, data=None):
    r = self.session.put(self.base_url + uri_path, data=data)
    self._check_req_return(r)

  # fetch all items
  def fetch_all_items(self):
    '''Returns all items defined in openHAB except for group-items'''
    items = {}
    res = self.req_get('/items/')

    for i in res:
      # we ignore group-items for now
      if i['type'] == 'Group':
        continue

      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name):
    '''Returns an item with its state and type as fetched from openHAB'''
    json_data = self.get_item_raw(name)

    return self.json_to_item(json_data)

  def json_to_item(self, json_data):
    if json_data['type'] == 'Switch':
      return SwitchItem(self, json_data)
    elif json_data['type'] == 'DateTime':
      return DateTimeItem(self, json_data)
    elif json_data['type'] == 'Contact':
      return ContactItem(self, json_data)
    elif json_data['type'] == 'Number':
      return NumberItem(self, json_data)
    else:
      return Item(self, json_data)

  def get_item_raw(self, name):
    '''Private method for fetching a json configuration of an item'''
    return self.req_get('/items/' + name)
