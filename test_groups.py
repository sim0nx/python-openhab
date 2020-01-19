#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Łukasz Matuszek (c) 2020-present <mrniebochod@gmail.com>
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

import openhab

base_url = 'http://localhost:8080/rest'
openhab = openhab.OpenHAB(base_url)

# fetch all items
print(" - Print all items:")
all_items = openhab.fetch_all_items()
for i in all_items.values():
  print(i)

# fetch some group
lights_group = openhab.get_item("Lights")

print(" - Send command to group")
lights_group.on()

print(" - Update all lights to OFF")
for v in lights_group.members.values():
  v.update('OFF')

print(" - Print all lights:")
for v in lights_group.members.values():
  print(v)
