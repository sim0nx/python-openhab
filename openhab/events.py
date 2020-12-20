# -*- coding: utf-8 -*-
"""python classes for receiving events from openHAB SSE (server side events) REST API."""

#
# Alexey Grubauer (c) 2020 <alexey@ingenious-minds.at>
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

import typing
from dataclasses import dataclass
import openhab.types


EventType = typing.NewType('EventType', str)

RawItemEventType: EventType = EventType("RawItem")

ItemEventType: EventType = EventType("Item")
ItemStateEventType: EventType = EventType("ItemStateEvent")
ItemCommandEventType: EventType = EventType("ItemCommandEvent")
ItemStateChangedEventType: EventType = EventType("ItemStateChangedEvent")


EventSource = typing.NewType('EventSource', str)
EventSourceInternal: EventSource = EventSource("Internal")
EventSourceOpenhab: EventSource = EventSource("Openhab")

@dataclass
class RawItemEvent(object):

  item_name: str
  source = EventSourceOpenhab
  event_type: EventType
  content: typing.Dict




@dataclass
class ItemEvent(object):
    """The base class for all ItemEvents"""
    type = ItemEventType
    item_name: str
    source: EventSource
    value_datatype: typing.Type[openhab.types.CommandType]
    value: typing.Any
    value_raw: typing.Any
    unit_of_measure: str
    is_my_own_echo:bool


@dataclass
class ItemStateEvent(ItemEvent):
    """a Event representing a state event on a Item"""
    type = ItemStateEventType



@dataclass
class ItemCommandEvent(ItemEvent):
    """a Event representing a command event on a Item"""
    type = ItemCommandEventType




@dataclass
class ItemStateChangedEvent(ItemStateEvent):
    """a Event representing a state change event on a Item"""
    type = ItemStateChangedEventType
    old_value_datatype: typing.Type[openhab.types.CommandType]
    old_value_raw: str
    old_value: typing.Any
    old_unit_of_measure: str
