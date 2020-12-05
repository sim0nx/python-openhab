import typing
from dataclasses import dataclass


EventType= typing.NewType('EventType', str)
ItemEventType : EventType = EventType("Item")
ItemStateEventType : EventType = EventType("ItemState")
ItemCommandEventType : EventType = EventType("ItemCommand")
ItemStateChangedEventType : EventType = EventType("ItemStateChanged")


EventSource= typing.NewType('EventSource', str)
EventSourceInternal : EventSource = EventSource("Internal")
EventSourceOpenhab : EventSource = EventSource("Openhab")

@dataclass
class ItemEvent(object):
    type = ItemEventType
    itemname: str
    source: EventSource

@dataclass
class ItemStateEvent(ItemEvent):
    type = ItemStateEventType
    remoteDatatype: str
    newValue: typing.Any
    asUpdate:bool


@dataclass
class ItemCommandEvent(ItemEvent):
    type = ItemCommandEventType
    remoteDatatype: str
    newValue: typing.Any


@dataclass
class ItemStateChangedEvent(ItemStateEvent):
    type = ItemStateChangedEventType
    oldRemoteDatatype: str
    oldValue: typing.Any
