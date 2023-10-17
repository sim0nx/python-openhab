#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import openhab

base_url = 'http://192.168.2.11:8080/rest'
openhab = openhab.OpenHAB(base_url)

# fetch all items
item_state_persistent = openhab.get_item('actual_price',start_time=1697497200).persistence

print(item_state_persistent)
