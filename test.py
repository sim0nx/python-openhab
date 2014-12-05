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


import requests
import datetime
import openhab
from openhab import Item


base_url = 'http://localhost:8080/rest'


# fetch all items
items = {}
r = requests.get(base_url + '/items/', headers={'accept': 'application/json'}).json()
for i in r['item']:
  if i['type'] == 'GroupItem':
    continue

  if not i['name'] in items:
    e = Item.initj(base_url, i)
    items[i['name']] = e


# fetch other items, show how to toggle a switch
sunset = Item.init(base_url, 'Sunset')
sunrise = Item.init(base_url, 'Sunrise')
knx_day_night = Item.init(base_url, 'KNX_day_night')

now = datetime.datetime.now()

if now > sunrise.state and now < sunset.state:
  knx_day_night.on()
else:
  knx_day_night.off()

print knx_day_night.state
