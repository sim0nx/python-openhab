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

import logging
import re
import typing
import warnings

from sseclient import SSEClient
import threading
import requests
import weakref
import json
import time
from requests.auth import HTTPBasicAuth


import openhab.items
import openhab.events

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class OpenHAB:
  """openHAB REST API client."""

  def __init__(self, base_url: str,
               username: typing.Optional[str] = None,
               password: typing.Optional[str] = None,
               http_auth: typing.Optional[requests.auth.AuthBase] = None,
               timeout: typing.Optional[float] = None,
               auto_update: typing.Optional[bool] = False,
               max_echo_to_openhab_ms: typing.Optional[int] = 800) -> None:
    """Class Constructor.

    Args:
      base_url (str): The openHAB REST URL, e.g. http://example.com/rest
      username (str, optional): A optional username, used in conjunction with a optional
                      provided password, in case openHAB requires authentication.
      password (str, optional): A optional password, used in conjunction with a optional
                      provided username, in case openHAB requires authentication.
      http_auth (AuthBase, optional): An alternative to username/password pair, is to
                            specify a custom http authentication object of data_type :class:`requests.auth.AuthBase`.
      timeout (float, optional): An optional timeout for REST transactions
      auto_update (bool, optional): True: receive Openhab Item Events to actively get informed about changes.
      max_echo_to_openhab_ms (int, optional): interpret Events from openHAB which hold a state-value equal to items current state-value
                                              which are coming in within maxEchoToOpenhabMS milliseconds since our update/command as echos of our own update//command
    Returns:
      OpenHAB: openHAB class instance.
    """
    self.base_url = base_url
    self.events_url = "{}/events?topics=smarthome/items".format(base_url.strip('/'))
    self.autoUpdate = auto_update
    self.session = requests.Session()
    self.session.headers['accept'] = 'application/json'
    self.registered_items = weakref.WeakValueDictionary()

    if http_auth is not None:
      self.session.auth = http_auth
    elif not (username is None or password is None):
      self.session.auth = HTTPBasicAuth(username, password)

    self.timeout = timeout
    self.maxEchoToOpenhabMS = max_echo_to_openhab_ms

    self.logger = logging.getLogger(__name__)
    self.__keep_event_daemon_running__ = False
    self.eventListeners: typing.List[typing.Callable] = []
    if self.autoUpdate:
      self.__installSSEClient__()

  @staticmethod
  def _check_req_return(req: requests.Response) -> None:
    """Internal method for checking the return value of a REST HTTP request.

    Args:
      req (requests.Response): A requests Response object.

    Returns:
      None: Returns None if no error occurred; else raises an exception.

    Raises:
      ValueError: Raises a ValueError exception in case of a non-successful
                  REST request.
    """
    if not 200 <= req.status_code < 300:
      req.raise_for_status()

  def _parse_item(self, event: openhab.events.ItemEvent) -> None:
    """method to parse an ItemEvent from openhab.
        it interprets the received ItemEvent data.
        in case the item was previously registered it will then delegate further parsing of the event to item itself through a call of the items _processExternalEvent method

            Args:
                  event:openhab.events.ItemEvent holding the event data
        """
    if event.item_name in self.registered_items:
      item = self.registered_items[event.item_name]
      if item is None:
        self.logger.warning("item '{}' was removed in all scopes. Ignoring the events coming in for it.".format(event.item_name))
      else:
        item.process_external_event(event)
    else:
      self.logger.debug("item '{}' not registered. ignoring the arrived event.".format(event.item_name))

  def _parse_event(self, event_data: typing.Dict) -> None:
    """method to parse a event from openhab.
    it interprets the received event dictionary and populates an openhab.events.event Object.
    for Item events it then calls _parseItem for a more detailed interpretation of the received data
    then it informs all registered listeners of openhab events
        Args:
              event_data send by openhab in a Dict
    """
    log = logging.getLogger()
    if "type" in event_data:
      event_reason = event_data["type"]

      if event_reason in ["ItemCommandEvent", "ItemStateEvent", "ItemStateChangedEvent"]:
        item_name = event_data["topic"].split("/")[-2]
        event = None
        payload_data = json.loads(event_data["payload"])
        remote_datatype = payload_data["type"]
        new_value = payload_data["value"]
        log.debug("####### new Event arrived:")
        log.debug("item name:{}".format(item_name))
        log.debug("Event-type:{}".format(event_reason))
        log.debug("payloadData:{}".format(event_data["payload"]))

        if event_reason == "ItemStateEvent":
          event = openhab.events.ItemStateEvent(item_name=item_name,
                                                source=openhab.events.EventSourceOpenhab,
                                                remote_datatype=remote_datatype,
                                                new_value_raw=new_value,
                                                unit_of_measure="",
                                                new_value="",
                                                as_update=False)
        elif event_reason == "ItemCommandEvent":
          event = openhab.events.ItemCommandEvent(item_name=item_name,
                                                  source=openhab.events.EventSourceOpenhab,
                                                  remote_datatype=remote_datatype,
                                                  new_value_raw=new_value,
                                                  unit_of_measure="",
                                                  new_value="")

        elif event_reason in ["ItemStateChangedEvent"]:
          old_remote_datatype = payload_data["oldType"]
          old_value = payload_data["oldValue"]
          event = openhab.events.ItemStateChangedEvent(item_name=item_name,
                                                       source=openhab.events.EventSourceOpenhab,
                                                       remote_datatype=remote_datatype,
                                                       new_value_raw=new_value,
                                                       new_value="",
                                                       unit_of_measure="",
                                                       old_remote_datatype=old_remote_datatype,
                                                       old_value_raw=old_value,
                                                       old_value="",
                                                       old_unit_of_measure="",
                                                       as_update=False)
          log.debug("received ItemStateChanged for '{itemname}'[{olddatatype}->{datatype}]:{oldState}->{newValue}".format(
            itemname=item_name,
            olddatatype=old_remote_datatype,
            datatype=remote_datatype,
            oldState=old_value,
            newValue=new_value))

        else:
          log.debug("received command for '{itemname}'[{datatype}]:{newValue}".format(itemname=item_name, datatype=remote_datatype, newValue=new_value))

        self._parse_item(event)
        self._inform_event_listeners(event)
    else:
      log.debug("received unknown Event-data_type in Openhab Event stream: {}".format(event_data))

  def _inform_event_listeners(self, event: openhab.events.ItemEvent):
    """internal method to send itemevents to listeners.
          Args:
                event:openhab.events.ItemEvent to be sent to listeners
        """
    for aListener in self.eventListeners:
      try:
        aListener(event)
      except Exception as e:
        self.logger.error("error executing Eventlistener for event:{}.".format(event.item_name), e)

  def add_event_listener(self, listener: typing.Callable[[openhab.events.ItemEvent], None]):
    """method to register a callback function to get informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] a method with one parameter of data_type openhab.events.ItemEvent which will be called for every event
        """
    self.eventListeners.append(listener)

  def remove_event_listener(self, listener: typing.Optional[typing.Callable[[openhab.events.ItemEvent], None]] = None):
    """method to unregister a callback function to stop getting informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] the method to be removed.
        """
    if listener is None:
      self.eventListeners.clear()
    elif listener in self.eventListeners:
      self.eventListeners.remove(listener)

  def _sse_daemon_thread(self):
    """internal method to receive events from openhab.
    This method blocks and therefore should be started as separate thread.
    """
    self.logger.info("starting Openhab - Event Daemon")
    next_waittime = initial_waittime = 0.1
    while self.__keep_event_daemon_running__:
      try:
        self.logger.info("about to connect to Openhab Events-Stream.")

        messages = SSEClient(self.events_url)

        next_waittime = initial_waittime
        for event in messages:
          event_data = json.loads(event.data)
          self._parse_event(event_data)
          if not self.__keep_event_daemon_running__:
            return

      except Exception as e:
        self.logger.warning("Lost connection to Openhab Events-Stream.", e)
        time.sleep(next_waittime)  # sleep a bit and then retry
        next_waittime = min(10, next_waittime+0.5)  # increase waittime over time up to 10 seconds

  def get_registered_items(self) -> weakref.WeakValueDictionary:
    """get a Dict of weak references to registered items.
            Args:
              an Item object
        """
    return self.registered_items

  def register_item(self, item: openhab.items.Item) -> None:
    """method to register an instantiated item. registered items can receive commands an updated from openhab.
    Usually you don´t need to register as Items register themself.
        Args:
          an Item object
    """
    if item is not None and item.name is not None:
      if item.name not in self.registered_items:
        self.registered_items[item.name] = item

  def __installSSEClient__(self) -> None:
    """ installs an event Stream to receive all Item events"""

    # now start readerThread
    self.__keep_event_daemon_running__ = True
    self.sseDaemon = threading.Thread(target=self._sse_daemon_thread, args=(), daemon=True)
    self.sseDaemon.start()

  def req_get(self, uri_path: str) -> typing.Any:
    """Helper method for initiating a HTTP GET request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the GET request.

    Returns:
      dict: Returns a dict containing the data returned by the OpenHAB REST server.
    """
    r = self.session.get(self.base_url + uri_path, timeout=self.timeout)
    self._check_req_return(r)
    return r.json()

  def req_post(self, uri_path: str, data: typing.Optional[dict] = None) -> None:
    """Helper method for initiating a HTTP POST request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the POST request.
      data (dict, optional): A optional dict with data to be submitted as part of the POST request.

    Returns:
      None: No data is returned.
    """
    r = self.session.post(self.base_url + uri_path, data=data, headers={'Content-Type': 'text/plain'}, timeout=self.timeout)
    self._check_req_return(r)

  def req_json_put(self, uri_path: str, json_data: str = None) -> None:
    """Helper method for initiating a HTTP PUT request.

        Besides doing the actual request, it also checks the return value and returns the resulting decoded
        JSON data.

        Args:
          uri_path (str): The path to be used in the PUT request.
          json_data (str): the request data as jason


        Returns:
          None: No data is returned.
        """

    r = self.session.put(self.base_url + uri_path, data=json_data, headers={'Content-Type': 'application/json', "Accept": "application/json"}, timeout=self.timeout)
    self._check_req_return(r)

  def req_del(self,  uri_path: str) -> None:
    """Helper method for initiating a HTTP DELETE request.

        Besides doing the actual request, it also checks the return value and returns the resulting decoded
        JSON data.

        Args:
          uri_path (str): The path to be used in the DELETE request.


        Returns:
          None: No data is returned.
        """
    r = self.session.delete(self.base_url + uri_path, headers={"Accept": "application/json"})
    self._check_req_return(r)

  def req_put(self, uri_path: str, data: typing.Optional[dict] = None) -> None:
    """Helper method for initiating a HTTP PUT request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the PUT request.
      data (dict, optional): A optional dict with data to be submitted as part of the PUT request.

    Returns:
      None: No data is returned.
    """
    r = self.session.put(self.base_url + uri_path, data=data, headers={'Content-Type': 'text/plain'}, timeout=self.timeout)
    self._check_req_return(r)

  # fetch all items
  def fetch_all_items(self) -> typing.Dict[str, openhab.items.Item]:
    """Returns all items defined in openHAB.

    Returns:
      dict: Returns a dict with item names as key and item class instances as value.
    """
    items = {}  # data_type: dict
    res = self.req_get('/items/')

    for i in res:
      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name: str) -> openhab.items.Item:
    """Returns an item with its state and data_type as fetched from openHAB.

    Args:
      name (str): The name of the item to fetch from openHAB.

    Returns:
      Item: A corresponding Item class instance with the state of the requested item.
    """
    json_data = self.get_item_raw(name)

    return self.json_to_item(json_data)

  def json_to_item(self, json_data: dict) -> openhab.items.Item:
    """This method takes as argument the RAW (JSON decoded) response for an openHAB item.

    It checks of what data_type the item is and returns a class instance of the
    specific item filled with the item's state.

    Args:
      json_data (dict): The JSON decoded data as returned by the openHAB server.

    Returns:
      Item: A corresponding Item class instance with the state of the item.
    """
    _type = json_data['type']
    if _type == 'Group' and 'groupType' in json_data:
      _type = json_data["groupType"]

    if _type == 'Switch':
      return openhab.items.SwitchItem(self, json_data)

    if _type == 'DateTime':
      return openhab.items.DateTimeItem(self, json_data)

    if _type == 'Contact':
      return openhab.items.ContactItem(self, json_data)

    if _type.startswith('Number'):
      if _type.startswith('Number:'):
        m = re.match(r'''^([^\s]+)''', json_data['state'])

        if m:
          json_data['state'] = m.group(1)

      return openhab.items.NumberItem(self, json_data)

    if _type == 'Dimmer':
      return openhab.items.DimmerItem(self, json_data)

    if _type == 'Color':
      return openhab.items.ColorItem(self, json_data)

    if _type == 'Rollershutter':
      return openhab.items.RollershutterItem(self, json_data)

    if _type == 'Player':
      return openhab.items.PlayerItem(self, json_data)

    return openhab.items.Item(self, json_data)

  def get_item_raw(self, name: str) -> typing.Any:
    """Private method for fetching a json configuration of an item.

    Args:
      name (str): The item name to be fetched.

    Returns:
      dict: A JSON decoded dict.
    """
    return self.req_get('/items/{}'.format(name))


# noinspection PyPep8Naming
class openHAB(OpenHAB):
  """Legacy class wrapper."""

  def __init__(self, *args, **kwargs):
    """Constructor."""
    super().__init__(*args, **kwargs)

    warnings.warn('The use of the "openHAB" class is deprecated, please use "OpenHAB" instead.', DeprecationWarning)
