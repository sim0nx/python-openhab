#!/usr/bin/env python3

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


import datetime
import json

import openhab

base_url = 'http://localhost:8080/rest'
openhab = openhab.OpenHAB(base_url)

# fetch all items
items = openhab.fetch_all_items()

# fetch other items, show how to toggle a switch
sunset = items.get('Sunset')
sunrise = items.get('Sunrise')
knx_day_night = items.get('KNX_day_night')

now = datetime.datetime.now(datetime.timezone.utc)

if now > sunrise.state and now < sunset.state:
  knx_day_night.on()
else:
  knx_day_night.off()

print(knx_day_night.state)

# start_time for fetching persistence data
start_time = datetime.datetime.fromtimestamp(1695504300123 / 1000, tz=datetime.UTC)

# fetch persistence data using the OpenHAB client object
for k in openhab.get_item_persistence(knx_day_night.name,
                                      page_length=20,
                                      start_time=start_time
                                      ):
  print(json.dumps(k, indent=4))

# fetch persistence data using the item directly
for k in knx_day_night.persistence(page_length=20,
                                   start_time=start_time
                                   ):
  print(json.dumps(k, indent=4))
