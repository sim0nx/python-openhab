# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API."""

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

# pylint: disable=bad-indentation
from __future__ import annotations

import datetime
import inspect
import json
import logging
import re
import time
import typing

import dateutil.parser

import openhab.events
import openhab.exceptions
import openhab.types

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class ItemFactory:
  """A factory to get an Item from Openhab, create new or delete existing items in openHAB."""

  def __init__(self, openhab_client: openhab.client.OpenHAB):
    """Constructor.

    Args:
      openhab_client (openhab.OpenHAB): openHAB object.
    """
    self.openHABClient = openhab_client

  def create_or_update_item(self,
                            name: str,
                            data_type: typing.Union[str, typing.Type[Item]],
                            quantity_type: typing.Optional[str] = None,
                            label: typing.Optional[str] = None,
                            category: typing.Optional[str] = None,
                            tags: typing.Optional[typing.List[str]] = None,
                            group_names: typing.Optional[typing.List[str]] = None,
                            group_type: typing.Optional[str] = None,
                            function_name: typing.Optional[str] = None,
                            function_params: typing.Optional[typing.List[str]] = None
                            ) -> Item:
    """Creates a new item in openhab if there is no item with name 'name' yet.

    If there is an item with 'name' already in openhab, the item gets updated with the infos provided. be aware that not provided fields will be deleted in openhab.
    Consider to get the existing item via 'getItem' and then read out existing fields to populate the parameters here.

    This function blocks until the item is created.

    Args:
      name (str): unique name of the item
      data_type ( str or any Itemclass): the type used in openhab (like Group, Number, Contact, DateTime, Rollershutter, Color, Dimmer, Switch, Player)
                       server.
                       To create groups use the itemtype 'Group'!
      quantity_type (str): optional quantity_type ( like Angle, Temperature, Illuminance (see https://www.openhab.org/docs/concepts/units-of-measurement.html))
      label (str): optional openhab label (see https://www.openhab.org/docs/configuration/items.html#label)
      category (str): optional category. no documentation found
      tags (List of str): optional list of tags (see https://www.openhab.org/docs/configuration/items.html#tags)
      group_names (List of str): optional list of groups this item belongs to.
      group_type (str): optional group_type. no documentation found
      function_name (str): optional function_name. no documentation found
      function_params (List of str): optional list of function Params. no documentation found

    Returns:
      the created Item
    """
    self.create_or_update_item_async(name=name,
                                     _type=data_type,
                                     quantity_type=quantity_type,
                                     label=label,
                                     category=category,
                                     tags=tags,
                                     group_names=group_names,
                                     group_type=group_type,
                                     function_name=function_name,
                                     function_params=function_params)

    time.sleep(0.05)
    retrycounter = 10
    while True:
      try:
        result = self.get_item(name)
        return result
      except Exception as e:
        retrycounter -= 1

        if retrycounter < 0:
          raise e

        time.sleep(0.05)

  def create_or_update_item_async(self,
                                  name: str,
                                  _type: typing.Union[str, typing.Type[Item]],
                                  quantity_type: typing.Optional[str] = None,
                                  label: typing.Optional[str] = None,
                                  category: typing.Optional[str] = None,
                                  tags: typing.Optional[typing.List[str]] = None,
                                  group_names: typing.Optional[typing.List[str]] = None,
                                  group_type: typing.Optional[str] = None,
                                  function_name: typing.Optional[str] = None,
                                  function_params: typing.Optional[typing.List[str]] = None
                                  ) -> None:
    """Creates a new item in openhab if there is no item with name 'name' yet.

    If there is an item with 'name' already in openhab, the item gets updated with the infos provided. be aware that not provided fields will be deleted in openhab.
    Consider to get the existing item via 'getItem' and then read out existing fields to populate the parameters here.

    This function does not wait for openhab to create the item. Use this function if you need to create many items quickly.

    Args:
      name (str): unique name of the item
      _type ( str or any Itemclass): the data_type used in openhab (like Group, Number, Contact, DateTime, Rollershutter, Color, Dimmer, Switch, Player)
                       server.
                       To create groups use the itemtype 'Group'!
      quantity_type (str): optional quantity_type ( like Angle, Temperature, Illuminance (see https://www.openhab.org/docs/concepts/units-of-measurement.html))
      label (str): optional openhab label (see https://www.openhab.org/docs/configuration/items.html#label)
      category (str): optional category. no documentation found
      tags (List of str): optional list of tags (see https://www.openhab.org/docs/configuration/items.html#tags)
      group_names (List of str): optional list of groups this item belongs to.
      group_type (str): optional group_type. no documentation found
      function_name (str): optional function_name. no documentation found
      function_params (List of str): optional list of function Params. no documentation found
    """
    paramdict: typing.Dict[str, typing.Union[str, typing.List[str], typing.Dict[str, typing.Union[str, typing.List]]]] = {}
    itemtypename = _type
    if inspect.isclass(_type):
      if issubclass(_type, Item):
        itemtypename = _type.TYPENAME

    if quantity_type is None:
      paramdict['type'] = itemtypename
    else:
      paramdict['type'] = '{}:{}'.format(itemtypename, quantity_type)

    paramdict['name'] = name

    if label is not None:
      paramdict['label'] = label

    if category is not None:
      paramdict['category'] = category

    if tags is not None:
      paramdict['tags'] = tags

    if group_names is not None:
      paramdict['groupNames'] = group_names

    if group_type is not None:
      paramdict['groupType'] = group_type

    if function_name is not None and function_params is not None:
      paramdict['function'] = {'name': function_name, 'params': function_params}

    json_body = json.dumps(paramdict)
    logging.getLogger(__name__).debug('about to create item with PUT request:{}'.format(json_body))
    self.openHABClient.req_json_put('/items/{}'.format(name), json_data=json_body)

  def get_item(self, itemname: str, force_request_to_openhab: typing.Optional[bool] = False) -> Item:
    """Get a existing openHAB item.

    Args:
        itemname (str): Unique name of the item
        force_request_to_openhab: Always fetch a fresh copy of the item from openHAB
    Returns:
      Item: the Item
    """
    return self.openHABClient.get_item(name=itemname, force_request_to_openhab=force_request_to_openhab)

  def fetch_all_items(self) -> typing.Dict[str, openhab.items.Item]:
    """Returns all items defined in openHAB.

    Returns:
      dict: Returns a dict with item names as key and item class instances as value.
    """
    return self.openHABClient.fetch_all_items()


class Item:
  """Base item class."""

  types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  command_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []
  state_changed_event_types: typing.Sequence[typing.Type[openhab.types.CommandType]] = []

  TYPENAME = 'unknown'

  def __init__(self, openhab_conn: 'openhab.client.OpenHAB', json_data: dict, auto_update: typing.Optional[bool] = True) -> None:
    """Constructor.

    Args:
      openhab_conn (openhab.OpenHAB): openHAB object.
      json_data (dic): A dict converted from the JSON data returned by the openHAB server.
      auto_update: Auto-update item states using an event stream listener.
    """
    self.openhab = openhab_conn
    self.autoUpdate = auto_update
    self.type_: typing.Optional[str] = None

    self.quantityType: typing.Optional[str] = None
    self.editable = None
    self.label = ''
    self.category = ''
    self.tags = ''
    self.groupNames = ''
    self._unitOfMeasure = ''
    self.group = False
    self.name = ''
    self._state = None  # type: typing.Optional[typing.Any]
    self._raw_state = None  # type: typing.Optional[typing.Any]  # raw state as returned by the server
    self._raw_state_event: typing.Optional[str] = None  # raw state as received from Serverevent
    self._members = {}  # type: typing.Dict[str, typing.Any] #  group members (key = item name), for none-group items it's empty

    self.logger = logging.getLogger(__name__)

    self.init_from_json(json_data)
    self.last_command_sent_time = datetime.datetime.fromtimestamp(0)
    self.last_command_sent = ''
    self.openhab.register_item(self)
    self.event_listeners: typing.Dict[typing.Callable[[openhab.items.Item, openhab.events.ItemEvent], None], EventListener] = {}

  def init_from_json(self, json_data: dict) -> None:
    """Initialize this object from a json configuration as fetched from openHAB.

    Args:
      json_data (dict): A dict converted from the JSON data returned by the openHAB
                        server.
    """
    self.name = json_data['name']
    if json_data['type'] == 'Group':
      self.group = True
      if 'groupType' in json_data:
        self.type_ = json_data['groupType']
      # init members
      for i in json_data['members']:
        self.members[i['name']] = self.openhab.json_to_item(i)

    else:
      self.type_ = json_data.get('type', None)

      if self.type_ is None:
        raise openhab.exceptions.InvalidReturnException('Item did not return a type attribute.')

      parts = self.type_.split(':')
      if len(parts) == 2:
        self.quantityType = parts[1]

    if 'editable' in json_data:
      self.editable = json_data['editable']
    if 'label' in json_data:
      self.label = json_data['label']
    if 'category' in json_data:
      self.category = json_data['category']
    if 'tags' in json_data:
      self.tags = json_data['tags']
    if 'groupNames' in json_data:
      self.groupNames = json_data['groupNames']

    self._raw_state = json_data['state']

    if self.is_undefined(self._raw_state):
      self._state = None
    else:
      self._state, self._unitOfMeasure = self._parse_rest(self._raw_state)

  @property
  def state(self) -> typing.Any:
    """The state property represents the current state of the item.

    The state is automatically refreshed from openHAB through incoming events if auto_update is turned on.
    If auto_update is turned off, the state gets refreshed now.
    Updating the value via this property sends an update to the event bus.
    """
    if not self.autoUpdate:
      json_data = self.openhab.get_item_raw(self.name)
      self.init_from_json(json_data)

    return self._state

  @state.setter
  def state(self, value: typing.Any) -> None:
    self.update(value)

  @property
  def members(self) -> typing.Dict[str, typing.Any]:
    """If item is a type of Group, it will return all member items for this group.

    For none group item empty dictionary will be returned.

    Returns:
      dict: Returns a dict with item names as key and `Item` class instances as value.

    """
    return self._members

  def _validate_value(self, value: typing.Union[str, typing.Type[openhab.types.CommandType]]) -> None:
    """Private method for verifying the new value before modifying the state of the item."""
    if self.type_ == 'String':
      if not isinstance(value, (str, bytes)):
        raise ValueError()
    elif self.types:
      validation = False

      for type_ in self.types:
        try:
          type_.validate(value)
        except ValueError:
          pass
        else:
          validation = True

      if not validation:
        raise ValueError('Invalid value "{}"'.format(value))
    else:
      raise ValueError()

  def _parse_rest(self, value: str) -> typing.Tuple[str, str]:
    """Parse a REST result into a native object."""
    return value, ''

  def _rest_format(self, value: str) -> typing.Union[str, bytes]:
    """Format a value before submitting to openHAB."""
    _value = value  # type: typing.Union[str, bytes]

    # Only latin-1 encoding is supported by default. If non-latin-1 characters were provided, convert them to bytes.
    try:
      _ = value.encode('latin-1')
    except UnicodeError:
      _value = value.encode('utf-8')

    return _value

  def _is_my_own_echo(self, event: openhab.events.ItemEvent) -> bool:
    """Find out if the incoming event is actually just a echo of my previous command or update."""
    now = datetime.datetime.now()
    result = None
    try:
      if event.source != openhab.events.EventSourceOpenhab:
        return True
      if self.last_command_sent_time + datetime.timedelta(milliseconds=self.openhab.maxEchoToOpenhabMS) > now:
        if event.type == openhab.events.ItemCommandEventType:
          if self.last_command_sent == event.value:
            # this is the echo of the command we just sent to openHAB.
            return True

          self.logger.debug('it is not an echo. last command sent:{}, eventvalue:{}'.format(self.last_command_sent, event.value))

        elif event.type in [openhab.events.ItemStateChangedEventType, openhab.events.ItemStateEventType]:
          if self._state == event.value:
            # this is the echo of the command we just sent to openHAB.
            return True

          self.logger.debug('it is not an echo. previous state:{}, eventvalue:{}'.format(self._state, event.value))

      return False

    finally:
      self.logger.debug(
        'checking if it is my own echo result:{result} for item:{itemname}, event.source:{source}, event.data_type{datatype}, self._state:{state}, event.new_value:{value}, self.last_command_sent_time:{last_command_sent_time}, now:{now}'.format(
          result=result,
          itemname=event.item_name,
          source=event.source,
          datatype=event.type,
          state=self._state,
          value=event.value,
          last_command_sent_time=self.last_command_sent_time,
          now=now))

  def delete(self) -> None:
    """Deletes the item from openHAB."""
    self.openhab.req_del('/items/{}'.format(self.name))
    self.openhab.unregister_item(self.name)
    self._state = None
    self.remove_all_event_listeners()

  @staticmethod
  def __extract_value_and_unitofmeasure(value: str) -> typing.Tuple[str, str]:
    """Private method to extract value and unit of measurement.

    Args:
      value (str): the parsed value

    Returns:
      tuple[str,str] : 2 strings containing the value and the unit of measure
    """
    if isinstance(value, tuple):
      value_result = value[0]
      uom = value[1]
      return value_result, uom

    return value, ''

  def _digest_external_command_event(self, command_type_class: typing.Type[openhab.types.CommandType], command: str) -> openhab.events.ItemCommandEvent:
    """Private method to process a command event coming from openHAB.

    Args:
      command_type_class (openhab.types.CommandType): the fitting CommandType to correctly process the command
      command (str): the received command

    Returns:
      openhab.events.ItemCommandEvent: the populated event
    """
    parsed_value = command_type_class.parse(command)
    value_result, uom = self.__extract_value_and_unitofmeasure(parsed_value)
    is_non_value_command = False
    if command_type_class not in self.state_changed_event_types + self.state_event_types:
      is_non_value_command = True
    item_command_event = openhab.events.ItemCommandEvent(item_name=self.name,
                                                         source=openhab.events.EventSourceOpenhab,
                                                         value_datatype=command_type_class,
                                                         value=value_result,
                                                         unit_of_measure=uom,
                                                         value_raw=command,
                                                         is_my_own_echo=False,
                                                         is_non_value_command=is_non_value_command)
    item_command_event.is_my_own_echo = self._is_my_own_echo(item_command_event)
    if command_type_class in self.state_types:
      if not item_command_event.is_my_own_echo:
        self.__set_state(value_result)
        self._unitOfMeasure = uom
    return item_command_event

  def digest_external_state_event(self, state_type_class: typing.Type[openhab.types.CommandType], value: str) -> openhab.events.ItemStateEvent:
    """Private method to process a state event coming from openHAB.

    Args:
      state_type_class (openhab.types.CommandType): the fitting CommandType to correctly process the value
      value (str): the received new state

    Returns:
      openhab.events.ItemStateEvent : the populated event
    """
    parsed_value = state_type_class.parse(value)
    value_result, uom = self.__extract_value_and_unitofmeasure(parsed_value)
    is_non_value_command = False
    if state_type_class not in self.state_changed_event_types + self.state_event_types:
      is_non_value_command = True
    item_state_event = openhab.events.ItemStateEvent(item_name=self.name,
                                                     source=openhab.events.EventSourceOpenhab,
                                                     value_datatype=state_type_class,
                                                     value=value_result,
                                                     unit_of_measure=uom,
                                                     value_raw=value,
                                                     is_my_own_echo=False,
                                                     is_non_value_command=is_non_value_command)

    item_state_event.is_my_own_echo = self._is_my_own_echo(item_state_event)
    if item_state_event in self.state_types:
      if not item_state_event.is_my_own_echo:
        self.__set_state(value_result)
        self._unitOfMeasure = uom
    return item_state_event

  def digest_external_state_changed_event(self, state_type_class: typing.Type[openhab.types.CommandType], value: str, old_state_type_class: typing.Type[openhab.types.CommandType], old_value: str) -> openhab.events.ItemStateChangedEvent:
    """Private method to process a state changed event coming from openHAB.

    Args:
      state_type_class (openhab.types.CommandType): the fitting CommandType to correctly process the value
      value (str): the new state
      old_state_type_class (openhab.types.CommandType): the fitting CommandType to correctly process the old_value
      old_value (str): the old state

    Returns:
      openhab.events.ItemStateChangedEvent : the populated event
    """
    parsed_value = state_type_class.parse(value)
    value_result, uom = self.__extract_value_and_unitofmeasure(parsed_value)
    old_value_result = old_uom = ''
    if old_state_type_class is not None:
      parsed_old_value = old_state_type_class.parse(old_value)
      old_value_result, old_uom = self.__extract_value_and_unitofmeasure(parsed_old_value)
    is_non_value_command = False
    if state_type_class not in self.state_changed_event_types + self.state_event_types:
      is_non_value_command = True
    item_state_changed_event = openhab.events.ItemStateChangedEvent(item_name=self.name,
                                                                    source=openhab.events.EventSourceOpenhab,
                                                                    value_datatype=state_type_class,
                                                                    value=value_result,
                                                                    unit_of_measure=uom,
                                                                    value_raw=value,
                                                                    old_value_datatype=old_state_type_class,
                                                                    old_value=old_value_result,
                                                                    old_unit_of_measure=old_uom,
                                                                    old_value_raw=old_value,
                                                                    is_my_own_echo=False,
                                                                    is_non_value_command=is_non_value_command)

    item_state_changed_event.is_my_own_echo = self._is_my_own_echo(item_state_changed_event)
    if item_state_changed_event in self.state_types:
      if not item_state_changed_event.is_my_own_echo:
        self._state = value_result
    return item_state_changed_event

  def _parse_external_command_event(self, raw_event: openhab.events.RawItemEvent) -> openhab.events.ItemCommandEvent:
    """Private method to process a command event coming from openHAB.

    Args:
      raw_event (openhab.events.RawItemEvent): the raw event
    Returns:
      openhab.events.ItemCommandEvent : the populated event
    """
    command_type = raw_event.content['type']
    command_type_class = openhab.types.CommandType.get_type_for(command_type)
    command = raw_event.content['value']
    if command_type_class in self.command_event_types:
      item_command_event = self._digest_external_command_event(command_type_class, command)
      return item_command_event
    raise Exception('unknown command event type')

  def _parse_external_state_event(self, raw_event: openhab.events.RawItemEvent) -> openhab.events.ItemStateEvent:
    """Private method to process a state event coming from openHAB.

    Args:
         raw_event (openhab.events.RawItemEvent): the raw event
    Returns:
      openhab.events.ItemStateEvent : the populated event
    """
    state_type = raw_event.content['type']
    state_type_class = openhab.types.CommandType.get_type_for(state_type)
    value = raw_event.content['value']
    if state_type_class in self.state_event_types:
      item_state_event = self.digest_external_state_event(state_type_class, value)
      return item_state_event
    raise Exception('unknown state event type')

  def _parse_external_state_changed_event(self, raw_event: openhab.events.RawItemEvent) -> openhab.events.ItemStateEvent:
    """Private method to process a state changed event coming from openHAB.

    Args:
         raw_event (openhab.events.RawItemEvent): the raw event
    Returns:
      openhab.events.ItemStateEvent : the populated event
    """
    state_changed_type = raw_event.content['type']
    state_changed_type_class = openhab.types.CommandType.get_type_for(state_changed_type)
    state_changed_old_type = raw_event.content['oldType']
    state_changed_old_type_class = openhab.types.CommandType.get_type_for(state_changed_old_type)
    value = raw_event.content['value']
    old_value = raw_event.content['oldValue']
    if state_changed_type_class in self.state_changed_event_types:
      item_state_changed_event = self.digest_external_state_changed_event(state_type_class=state_changed_type_class, value=value, old_state_type_class=state_changed_old_type_class, old_value=old_value)
      return item_state_changed_event
    raise Exception('unknown statechanged event type:{}'.format(state_changed_type_class))

  def _process_external_event(self, raw_event: openhab.events.RawItemEvent) -> None:
    """Private method to process a event coming from openHAB and inform all Listeners about the event.

    Args:
      raw_event (openhab.events.RawItemEvent): the raw event
    """
    if not self.autoUpdate:
      return

    self.logger.debug('processing external event:{}'.format(raw_event))

    if raw_event.event_type == openhab.events.ItemCommandEvent.type:
      event = self._parse_external_command_event(raw_event)
    elif raw_event.event_type == openhab.events.ItemStateChangedEvent.type:
      event = self._parse_external_state_changed_event(raw_event)
    elif raw_event.event_type == openhab.events.ItemStateEvent.type:
      event = self._parse_external_state_event(raw_event)
    else:
      raise NotImplementedError('Event type:{} is not implemented.'.format(raw_event.event_type))

    for aListener in self.event_listeners.values():
      if event.type in aListener.listeningTypes:
        if not event.is_my_own_echo or aListener.alsoGetMyEchosFromOpenHAB:
          try:
            aListener.callbackfunction(self, event)
          except Exception as e:
            self.logger.exception('error executing Eventlistener for item:{}.'.format(event.item_name), e)

  def _process_internal_event(self, event: openhab.events.ItemEvent) -> None:
    """Private method to process a event coming from local changes and inform all Listeners about the event.

    Args:
      event (openhab.events.ItemEvent): the internal event
    """
    self.logger.debug('processing internal event:{}'.format(event))
    for aListener in self.event_listeners.values():
      if event.type in aListener.listeningTypes:
        if aListener.onlyIfEventsourceIsOpenhab:
          continue

        try:
          aListener.callbackfunction(self, event)
        except Exception as e:
          self.logger.exception('error executing Eventlistener for item:{}.'.format(event.item_name), e)

  def add_event_listener(self,
                         listening_types: typing.Union[openhab.events.EventType, typing.Set[openhab.events.EventType]],
                         listener: typing.Callable[[openhab.items.Item, openhab.events.ItemEvent], None],
                         only_if_eventsource_is_openhab: bool = True,
                         also_get_my_echos_from_openhab: bool = False) -> None:
    """Add a Listener interested in changes of items happening in openHAB.

    Listener is a callable with 2 parameters:
      - item (openhab.items.Item): the item that received a command, change or update
      - event (openhab.events.ItemEvent): the item Event holding the actual change

    Args:
      listening_types (openhab.events.EventType or set of openhab.events.EventType): the eventTypes the listener is interested in.
      listener (Callable[[openhab.items.Item,openhab.events.ItemEvent],None]): a method with 2 parameters as described above
      only_if_eventsource_is_openhab (bool): the listener only wants events that are coming from openHAB.
      also_get_my_echos_from_openhab (bool): the listener also wants to receive events coming from openHAB that originally were triggered by commands or changes by our item itself.
    """
    if listener in self.event_listeners:
      event_listener = self.event_listeners[listener]
      event_listener.add_types(listening_types)
      event_listener.onlyIfEventsourceIsOpenhab = only_if_eventsource_is_openhab
    else:
      event_listener = EventListener(listening_types=listening_types, listener=listener, only_if_eventsource_is_openhab=only_if_eventsource_is_openhab, also_get_my_echos_from_openhab=also_get_my_echos_from_openhab)
      self.event_listeners[listener] = event_listener

  def remove_all_event_listeners(self) -> None:
    """Remove all event listeners from item."""
    self.event_listeners = {}

  def remove_event_listener(self,
                            types: typing.Union[openhab.events.EventType, typing.Set[openhab.events.EventType]],
                            listener: typing.Callable[[openhab.items.Item, openhab.events.ItemEvent], None]) -> None:
    """Removes a previously registered Listener interested in changes of items happening in openHAB.

    Args:
      types (openhab.events.EventType or set of openhab.events.EventType): the eventTypes the listener is interested in.
      listener: the previously registered listener method.
    """
    if listener in self.event_listeners:
      event_listener = self.event_listeners[listener]
      event_listener.remove_types(types)
      if not event_listener.listeningTypes:
        self.event_listeners.pop(listener)

  def is_undefined(self, value: str) -> bool:
    """Check if value is undefined."""
    for aStateType in self.state_types:
      if not aStateType.is_undefined(value):
        return False

    return True

  def __set_state(self, value: str) -> None:
    """Private method for setting the internal state."""
    if self.is_undefined(value):
      self._state = None
    else:
      self._state = value

  def __str__(self) -> str:
    """String representation."""
    return '<{0} - {1} : {2}>'.format(self.type_, self.name, self._state)

  def _update(self, value: typing.Any) -> None:
    """Updates the state of an item, input validation is expected to be already done.

    Args:
      value (object): The value to update the item with. The data_type of the value depends
                      on the item data_type and is checked accordingly.
    """
    # noinspection PyTypeChecker
    self.last_command_sent_time = datetime.datetime.now()
    self.last_command_sent = value
    self.openhab.req_put('/items/{}/state'.format(self.name), data=value)

  def update(self, value: typing.Any) -> None:
    """Updates the state of an item.

    Args:
      value (object): The value to update the item with. The data_type of the value depends
                      on the item data_type and is checked accordingly.
    """
    oldstate = self._state
    self._validate_value(value)

    v = self._rest_format(value)
    self._state = value
    self._update(v)

    if oldstate == self._state:
      event = openhab.events.ItemStateEvent(item_name=self.name,
                                            source=openhab.events.EventSourceInternal,
                                            value_datatype=self.type_,
                                            value=self._state,
                                            value_raw=None,
                                            unit_of_measure=self._unitOfMeasure,
                                            is_my_own_echo=False,
                                            is_non_value_command=False
                                            )
    else:
      event = openhab.events.ItemStateChangedEvent(item_name=self.name,
                                                   source=openhab.events.EventSourceInternal,
                                                   value_datatype=self.type_,
                                                   value=self._state,
                                                   value_raw=None,
                                                   unit_of_measure=self._unitOfMeasure,
                                                   old_value_datatype=self.type_,
                                                   old_value=oldstate,
                                                   old_value_raw='',
                                                   old_unit_of_measure='',
                                                   is_my_own_echo=False,
                                                   is_non_value_command=False
                                                   )
    self._process_internal_event(event)

  # noinspection PyTypeChecker
  def command(self, value: typing.Any) -> None:
    """Sends the given value as command to the event bus.

    Args:
      value (object): The value to send as command to the event bus. The data_type of the
                      value depends on the item data_type and is checked accordingly.
    """
    self._validate_value(value)
    v = self._rest_format(value)
    self._state = value
    self.last_command_sent_time = datetime.datetime.now()
    self.openhab.req_post('/items/{}'.format(self.name), data=v)

    unit_of_measure = ''
    if hasattr(self, '_unitOfMeasure'):
      unit_of_measure = self._unitOfMeasure
    event = openhab.events.ItemCommandEvent(item_name=self.name,
                                            source=openhab.events.EventSourceInternal,
                                            value_datatype=self.type_,
                                            value=value,
                                            value_raw=None,
                                            unit_of_measure=unit_of_measure,
                                            is_my_own_echo=True,
                                            is_non_value_command=False
                                            )
    self._process_internal_event(event)

  def update_state_null(self) -> None:
    """Update the state of the item to *NULL*."""
    self._update('NULL')

  def update_state_undef(self) -> None:
    """Update the state of the item to *UNDEF*."""
    self._update('UNDEF')

  def is_state_null(self) -> bool:
    """If the item state is None, use this method for checking if the remote value is NULL."""
    if self.state is None:
      # we need to query the current remote state as else this method will not work correctly if called after
      # either update_state method
      if self._raw_state is None:
        # This should never happen
        raise ValueError('Invalid internal (raw) state.')

      return self._raw_state == 'NULL'

    return False

  def is_state_undef(self) -> bool:
    """If the item state is None, use this method for checking if the remote value is UNDEF."""
    if self.state is None:
      # we need to query the current remote state as else this method will not work correctly if called after
      # either update_state method
      if self._raw_state is None:
        # This should never happen
        raise ValueError('Invalid internal (raw) state.')

      return self._raw_state == 'UNDEF'

    return False


class StringItem(Item):
  """DateTime item data_type."""

  types = [openhab.types.StringType]
  state_types = types
  command_event_types = types
  state_event_types = types
  state_changed_event_types = types

  TYPENAME = 'String'


class DateTimeItem(Item):
  """DateTime item data_type."""

  types = [openhab.types.DateTimeType]
  state_types = types
  command_event_types = types
  state_event_types = types
  state_changed_event_types = types

  TYPENAME = 'DateTime'

  def __gt__(self, other: datetime.datetime) -> bool:
    """Greater than comparison."""
    if self._state is None or not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state > other

  def __lt__(self, other: object) -> bool:
    """Less than comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return not self.__gt__(other)

  def __eq__(self, other: object) -> bool:
    """Equality comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return self._state == other

  def __ne__(self, other: object) -> bool:
    """Not equal comparison."""
    if not isinstance(other, datetime.datetime):
      raise NotImplementedError('You can only compare two DateTimeItem objects.')

    return not self.__eq__(other)

  def _parse_rest(self, value: str) -> typing.Tuple[datetime.datetime, str]:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a datetime.datetime object.

    Returns:
      datetime.datetime: The datetime.datetime object as converted from the string
                         parameter.
    """
    return dateutil.parser.parse(value), ''

  def _rest_format(self, value: datetime.datetime) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value (datetime.datetime): A datetime.datetime argument to be converted
                                 into a string.

    Returns:
      str: The string as converted from the datetime.datetime parameter.
    """
    # openHAB supports only up to milliseconds as of this writing
    return value.isoformat(timespec='milliseconds')


class PlayerItem(Item):
  """PlayerItem item data_type."""
  TYPENAME = 'Player'

  types = [openhab.types.PlayPauseType, openhab.types.NextPrevious, openhab.types.RewindFastforward]
  state_types = [openhab.types.PlayPauseType, openhab.types.RewindFastforward]
  command_event_types = [openhab.types.PlayPauseType, openhab.types.NextPrevious, openhab.types.RewindFastforward]
  state_event_types = [openhab.types.PlayPauseType, openhab.types.RewindFastforward]
  state_changed_event_types = [openhab.types.PlayPauseType, openhab.types.RewindFastforward]

  def play(self) -> None:
    """Send the command PLAY."""
    self.command(openhab.types.PlayPauseType.PLAY)

  def pause(self) -> None:
    """Send the command PAUSE."""
    self.command(openhab.types.PlayPauseType.PAUSE)

  def next(self) -> None:
    """Send the command NEXT."""
    self.command(openhab.types.NextPrevious.NEXT)

  def previous(self) -> None:
    """Send the command PREVIOUS."""
    self.command(openhab.types.NextPrevious.PREVIOUS)

  def fastforward(self) -> None:
    """Send the command FASTFORWARD."""
    self.command(openhab.types.RewindFastforward.FASTFORWARD)

  def rewind(self) -> None:
    """Send the command REWIND."""
    self.command(openhab.types.RewindFastforward.REWIND)


class SwitchItem(Item):
  """SwitchItem item data_type."""
  types = [openhab.types.OnOffType]
  state_types = types
  command_event_types = types
  state_event_types = types
  state_changed_event_types = types
  TYPENAME = 'Switch'

  def on(self) -> None:
    """Set the state of the switch to ON."""
    self.command(openhab.types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the switch to OFF."""
    self.command(openhab.types.OnOffType.OFF)

  def toggle(self) -> None:
    """Toggle the state of the switch to OFF to ON and vice versa."""
    if self.state == openhab.types.OnOffType.ON:
      self.off()
    elif self.state == openhab.types.OnOffType.OFF:
      self.on()


class NumberItem(Item):
  """NumberItem item data_type."""

  types = [openhab.types.DecimalType]
  state_types = types
  command_event_types = types
  state_event_types = types
  state_changed_event_types = types
  TYPENAME = 'Number'

  def _parse_rest(self, value: str) -> typing.Tuple[typing.Union[float, None], str]:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a float object.

    Returns:
      float: The float object as converted from the string parameter.
      str: The unit Of Measure or empty string
    """
    if value in ('UNDEF', 'NULL'):
      return None, ''
    # m = re.match(r'''^(-?[0-9.]+)''', value)
    try:
      m = re.match(r'(-?[0-9.]+)\s?(.*)?$', value)

      if m:
        value = m.group(1)
        unit_of_measure = m.group(2)

        return float(value), unit_of_measure

      return float(value), ''

    except Exception as e:
      self.logger.error('error in parsing new value "{}" for "{}"'.format(value, self.name), e)

    raise ValueError('{}: unable to parse value "{}"'.format(self.__class__, value))

  def _rest_format(self, value: float) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value (float): A float argument to be converted into a string.

    Returns:
      str: The string as converted from the float parameter.
    """
    return str(value)


class ContactItem(Item):
  """Contact item data_type."""

  types = [openhab.types.OpenCloseType]
  state_types = types
  command_event_types = types
  state_event_types = types
  state_changed_event_types = types
  TYPENAME = 'Contact'

  def command(self, *args: typing.Any, **kwargs: typing.Any) -> None:
    """This overrides the `Item` command method.

    Note: Commands are not accepted for items of data_type contact.
    """
    raise ValueError('This item ({}) only supports updates, not commands!'.format(self.__class__))

  def open(self) -> None:
    """Set the state of the contact item to OPEN."""
    self.state = openhab.types.OpenCloseType.OPEN

  def closed(self) -> None:
    """Set the state of the contact item to CLOSED."""
    self.state = openhab.types.OpenCloseType.CLOSED


class DimmerItem(Item):
  """DimmerItem item data_type."""

  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType]
  state_types = [openhab.types.PercentType]
  command_event_types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType]
  state_event_types = [openhab.types.OnOffType, openhab.types.PercentType]
  state_changed_event_types = [openhab.types.PercentType]
  TYPENAME = 'Dimmer'

  def _parse_rest(self, value: str) -> typing.Tuple[float, str]:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      int: The int object as converted from the string parameter.
    """
    return float(value), ''

  def _rest_format(self, value: typing.Union[str, int]) -> str:
    """Format a value before submitting to OpenHAB.

    Args:
      value: Either a string or an integer; in the latter case we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if not isinstance(value, str):
      return str(value)

    return value

  def on(self) -> None:
    """Set the state of the dimmer to ON."""
    self.command(openhab.types.OnOffType.ON)

  def off(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.OnOffType.OFF)

  def increase(self) -> None:
    """Increase the state of the dimmer."""
    self.command(openhab.types.IncreaseDecreaseType.INCREASE)

  def decrease(self) -> None:
    """Decrease the state of the dimmer."""
    self.command(openhab.types.IncreaseDecreaseType.DECREASE)


class ColorItem(DimmerItem):
  """ColorItem item data_type."""

  types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType, openhab.types.ColorType]
  state_types = [openhab.types.ColorType]
  command_event_types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.IncreaseDecreaseType, openhab.types.ColorType]
  state_event_types = [openhab.types.OnOffType, openhab.types.PercentType, openhab.types.ColorType]
  state_changed_event_types = [openhab.types.ColorType]
  TYPENAME = 'Color'

  def _parse_rest(self, value: str) -> typing.Tuple[typing.Tuple[int, int, float], str]:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a str object.

    Returns:
      str: The str object as converted from the string parameter.
    """
    result = openhab.types.ColorType.parse(value)
    return result, ""

  def _rest_format(self, value: typing.Union[str, int]) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value: Either a string or an integer; in the latter case we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if isinstance(value, tuple):
      if len(value) == 3:
        return "{},{},{}".format(value[0], value[1], value[2])
    if not isinstance(value, str):
      return str(value)

    return value

  @staticmethod
  def __extract_value_and_unitofmeasure(value: str) -> typing.Tuple[str, str]:
    return value, ''


class RollershutterItem(Item):
  """RollershutterItem item data_type."""

  types = [openhab.types.UpDownType, openhab.types.PercentType, openhab.types.StopMoveType]
  state_types = [openhab.types.PercentType]
  command_event_types = [openhab.types.UpDownType, openhab.types.StopMoveType, openhab.types.PercentType]
  state_event_types = [openhab.types.UpDownType, openhab.types.PercentType]
  state_changed_event_types = [openhab.types.PercentType]
  TYPENAME = 'Rollershutter'

  def _parse_rest(self, value: str) -> typing.Tuple[int, str]:
    """Parse a REST result into a native object.

    Args:
      value (str): A string argument to be converted into a int object.

    Returns:
      int: The int object as converted from the string parameter.
    """
    return int(float(value)), ''

  def _rest_format(self, value: typing.Union[str, int]) -> str:
    """Format a value before submitting to openHAB.

    Args:
      value: Either a string or an integer; in the latter case we have to cast it to a string.

    Returns:
      str: The string as possibly converted from the parameter.
    """
    if not isinstance(value, str):
      return str(value)

    return value

  def up(self) -> None:
    """Set the state of the dimmer to ON."""
    self.command(openhab.types.UpDownType.UP)

  def down(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.UpDownType.DOWN)

  def stop(self) -> None:
    """Set the state of the dimmer to OFF."""
    self.command(openhab.types.StopMoveType.STOP)


class EventListener:
  """EventListener Objects hold data about a registered event listener."""

  def __init__(self,
               listening_types: typing.Set[openhab.events.EventType],
               listener: typing.Callable[[openhab.items.Item, openhab.events.ItemEvent], None],
               only_if_eventsource_is_openhab: bool,
               also_get_my_echos_from_openhab: bool) -> None:
    """Constructor of an EventListener Object.

    Listener is a callable with 2 parameters:
      - item (openhab.items.Item): the item that received a command, change or update
      - event (openhab.events.ItemEvent): the item Event holding the actual change

    Args:
      listening_types (openhab.events.EventType or set of openhab.events.EventType): the eventTypes the listener is interested in.
      listener (Callable[[openhab.items.Item,openhab.events.ItemEvent],None]): a method with 2 parameters as described above
      only_if_eventsource_is_openhab (bool): the listener only wants events that are coming from openHAB.
      also_get_my_echos_from_openhab (bool): the listener also wants to receive events coming from openHAB that originally were triggered by commands or changes by our item itself.
    """
    all_types = {openhab.events.ItemStateEvent.type, openhab.events.ItemCommandEvent.type, openhab.events.ItemStateChangedEvent.type}
    if listening_types is None:
      self.listeningTypes = all_types
    elif not hasattr(listening_types, '__iter__'):
      self.listeningTypes = {listening_types}
    elif not listening_types:
      self.listeningTypes = all_types
    else:
      self.listeningTypes = listening_types

    self.callbackfunction: typing.Callable[[openhab.items.Item, openhab.events.ItemEvent], None] = listener
    self.onlyIfEventsourceIsOpenhab = only_if_eventsource_is_openhab
    self.alsoGetMyEchosFromOpenHAB = also_get_my_echos_from_openhab

  def add_types(self, listening_types: typing.Union[openhab.events.EventType, typing.Set[openhab.events.EventType]]) -> None:
    """Add aditional listening types.

    Args:
      listening_types (openhab.events.EventType or set of openhab.events.EventType): the additional eventTypes the listener is interested in.

    """
    if listening_types is None:
      return

    if not hasattr(listening_types, '__iter__'):
      self.listeningTypes.add(listening_types)
      return

    if not listening_types:
      return

    self.listeningTypes.update(listening_types)

  def remove_types(self, listening_types: typing.Union[openhab.events.EventType, typing.Set[openhab.events.EventType]]) -> None:
    """Remove listening types.

    Args:
      listening_types (openhab.events.EventType or set of openhab.events.EventType): the eventTypes the listener is not interested in anymore
    """
    if listening_types is None:
      self.listeningTypes.clear()
    elif not hasattr(listening_types, '__iter__'):
      self.listeningTypes.remove(listening_types)
    elif not listening_types:
      self.listeningTypes.clear()
    else:
      self.listeningTypes.difference_update(listening_types)
