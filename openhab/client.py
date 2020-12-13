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
from dataclasses import dataclass

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
               autoUpdate: typing.Optional[bool] = False,
               maxEchoToOpenHAB_ms: typing.Optional[int]=800) -> None:
    """Constructor.

    Args:
      base_url (str): The openHAB REST URL, e.g. http://example.com/rest
      username (str, optional): A optional username, used in conjunction with a optional
                      provided password, in case openHAB requires authentication.
      password (str, optional): A optional password, used in conjunction with a optional
                      provided username, in case openHAB requires authentication.
      http_auth (AuthBase, optional): An alternative to username/password pair, is to
                            specify a custom http authentication object of type :class:`requests.auth.AuthBase`.
      timeout (float, optional): An optional timeout for REST transactions
      autoUpdate (bool, optional): True: receive Openhab Item Events to actively get informed about changes.
      maxEchoToOpenHAB_ms (int, optional): interpret Events from openHAB which hold a state-value equal to items current state-value which are coming in within maxEchoToOpenhabMS millisends since our update/command as echos of our own update//command
    Returns:
      OpenHAB: openHAB class instance.
    """
    self.base_url = base_url
    self.events_url = "{}/events?topics=smarthome/items".format(base_url.strip('/'))
    self.autoUpdate=autoUpdate
    self.session = requests.Session()
    self.session.headers['accept'] = 'application/json'
    #self.registered_items:typing.Dict[str,openhab.items.Item]= {}
    self.registered_items = weakref.WeakValueDictionary()


    if http_auth is not None:
      self.session.auth = http_auth
    elif not (username is None or password is None):
      self.session.auth = HTTPBasicAuth(username, password)

    self.timeout = timeout
    self.maxEchoToOpenhabMS=maxEchoToOpenHAB_ms

    self.logger = logging.getLogger(__name__)
    self.__keep_event_deamon_running__ = False
    self.eventListeners:typing.List[typing.Callable] = []
    if self.autoUpdate:
      self.__installSSEClient__()

  @staticmethod
  def _check_req_return(req: requests.Response) -> None:
    """Internal method for checking the return value of a REST HTTP request.

    Args:
      req (requests.Response): A requests Response object.

    Returns:
      None: Returns None if no error occured; else raises an exception.

    Raises:
      ValueError: Raises a ValueError exception in case of a non-successful
                  REST request.
    """
    if not (200 <= req.status_code < 300):
      logging.getLogger().error(req.content)
      req.raise_for_status()



  def _parseItem(self, event:openhab.events.ItemEvent)->None:
    """method to parse an ItemEvent from openhab.
        it interprets the received ItemEvent data.
        in case the item was previously registered it will then delegate further parsing of the event to item iteself through a call of the items _processExternalEvent method

            Args:
                  event:openhab.events.ItemEvent holding the eventdata
        """
    if event.itemname in self.registered_items:
      item=self.registered_items[event.itemname]
      if item is None:
        self.logger.warning("item '{}' was removed in all scopes. Ignoring the events coming in for it.".format(event.itemname))
      else:
        item._processExternalEvent(event)
    else:
      self.logger.debug("item '{}' not registered. ignoring the arrived event.".format(event.itemname))









  def _parseEvent(self, eventData:typing.Dict)->None:
    """method to parse a event from openhab.
    it interprets the received event dictionary and populates an openhab.events.event Object.
    for Itemevents it then calls _parseItem for a more detailed interpretation of the received data
    then it informs all registered listeners of openhab events
        Args:
              eventData send by openhab in a Dict
    """
    log=logging.getLogger()
    eventreason=eventData["type"]



    if eventreason  in ["ItemCommandEvent","ItemStateEvent","ItemStateChangedEvent"]:
      itemname = eventData["topic"].split("/")[-2]
      event=None
      payloadData = json.loads(eventData["payload"])
      remoteDatatype = payloadData["type"]
      newValue = payloadData["value"]
      log.debug("####### new Event arrived:")
      log.debug("item name:{}".format(itemname))
      log.debug("type:{}".format(eventreason))
      log.debug("payloadData:{}".format(eventData["payload"]))

      if eventreason =="ItemStateEvent":
        event = openhab.events.ItemStateEvent(itemname=itemname, source=openhab.events.EventSourceOpenhab, remoteDatatype=remoteDatatype,newValueRaw=newValue,unitOfMeasure="",newValue="",asUpdate=False)
      elif eventreason =="ItemCommandEvent":
        event = openhab.events.ItemCommandEvent(itemname=itemname, source=openhab.events.EventSourceOpenhab, remoteDatatype=remoteDatatype, newValueRaw=newValue,unitOfMeasure="", newValue="")
      elif eventreason in ["ItemStateChangedEvent"]:
        oldremoteDatatype = payloadData["oldType"]
        oldValue = payloadData["oldValue"]
        event=openhab.events.ItemStateChangedEvent(itemname=itemname,source=openhab.events.EventSourceOpenhab, remoteDatatype=remoteDatatype,newValueRaw=newValue,newValue="",unitOfMeasure="",oldRemoteDatatype=oldremoteDatatype,oldValueRaw=oldValue, oldValue="", oldUnitOfMeasure="",asUpdate=False)
        log.debug("received ItemStateChanged for '{itemname}'[{olddatatype}->{datatype}]:{oldState}->{newValue}".format(itemname=itemname, olddatatype=oldremoteDatatype, datatype=remoteDatatype, oldState=oldValue, newValue=newValue))

      else:
        log.debug("received command for '{itemname}'[{datatype}]:{newValue}".format(itemname=itemname, datatype=remoteDatatype, newValueRaw=newValue))

      self._parseItem(event)
      self._informEventListeners(event)
    else:
      log.info("received unknown Event-type in Openhab Event stream: {}".format(eventData))

  def _informEventListeners(self, event:openhab.events.ItemEvent):
    """internal method to send itemevents to listeners.
          Args:
                event:openhab.events.ItemEvent to be sent to listeners
        """
    for aListener in self.eventListeners:
      try:
        aListener(event)
      except Exception as e:
        self.logger.error("error executing Eventlistener for event:{}.".format(event.itemname),e)

  def addEventListener(self, listener:typing.Callable[[openhab.events.ItemEvent],None]):
    """method to register a callback function to get informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] a method with one parameter of type openhab.events.ItemEvent which will be called for every event
        """
    self.eventListeners.append(listener)

  def removeEventListener(self, listener:typing.Optional[typing.Callable[[openhab.events.ItemEvent],None]]=None):
    """method to unregister a callback function to stop getting informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] the method to be removed.
        """
    if listener is None:
      self.eventListeners.clear()
    elif listener in self.eventListeners:
      self.eventListeners.remove(listener)






  def _sseDaemonThread(self):
    """internal method to receive events from openhab.
    This method blocks and therefore should be started as separate thread.
    """
    self.logger.info("starting Openhab - Event Deamon")
    next_waittime=initial_waittime=0.1
    while self.__keep_event_deamon_running__:
      try:
        self.logger.info("about to connect to Openhab Events-Stream.")

        messages = SSEClient(self.events_url)

        next_waittime = initial_waittime
        for event in messages:
          eventData = json.loads(event.data)
          self._parseEvent(eventData)
          if not self.__keep_event_deamon_running__:
            return

      except Exception as e:
        self.logger.warning("Lost connection to Openhab Events-Stream.",e)
        time.sleep(next_waittime) # aleep a bit and then retry
        next_waittime=min(10,next_waittime+0.5) # increase waittime over time up to 10 seconds



  def get_registered_items(self)->weakref.WeakValueDictionary:
    """get a Dict of weak references to registered items.
            Args:
              an Item object
        """
    return self.registered_items

  def register_item(self, item: openhab.items.Item)->None:
    """method to register an instantiated item. registered items can receive commands an updated from openhab.
    Usually you don´t need to register as Items register themself.
        Args:
          an Item object
    """
    if not item is None and not item.name is None:
      if not item.name in self.registered_items:
        #self.registered_items[item.name]=weakref.ref(item)
        self.registered_items[item.name] = item

  def __installSSEClient__(self)->None:
    """ installs an event Stream to receive all Item events"""

    #now start readerThread
    self.__keep_event_deamon_running__=True
    self.sseDaemon = threading.Thread(target=self._sseDaemonThread, args=(), daemon=True)
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

    return None

  def req_json_put(self, uri_path: str, jsonData: str = None) -> None:
    """Helper method for initiating a HTTP PUT request.

        Besides doing the actual request, it also checks the return value and returns the resulting decoded
        JSON data.

        Args:
          uri_path (str): The path to be used in the PUT request.
          jsondata (str): the request data as jason


        Returns:
          None: No data is returned.
        """

    r = self.session.put(self.base_url + uri_path, data=jsonData, headers={'Content-Type': 'application/json', "Accept": "application/json"}, timeout=self.timeout)
    self._check_req_return(r)

  def req_del(self,  uri_path: str)->None:
    """Helper method for initiating a HTTP DELETE request.

        Besides doing the actual request, it also checks the return value and returns the resulting decoded
        JSON data.

        Args:
          uri_path (str): The path to be used in the DELETE request.


        Returns:
          None: No data is returned.
        """
    r= self.session.delete(self.base_url + uri_path,headers={"Accept": "application/json"})
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

    return None

  # fetch all items
  def fetch_all_items(self) -> typing.Dict[str, openhab.items.Item]:
    """Returns all items defined in openHAB.

    Returns:
      dict: Returns a dict with item names as key and item class instances as value.
    """
    items = {}  # type: dict
    res = self.req_get('/items/')

    for i in res:
      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name: str) -> openhab.items.Item:
    """Returns an item with its state and type as fetched from openHAB.

    Args:
      name (str): The name of the item to fetch from openHAB.

    Returns:
      Item: A corresponding Item class instance with the state of the requested item.
    """
    json_data = self.get_item_raw(name)

    return self.json_to_item(json_data)

  def json_to_item(self, json_data: dict) -> openhab.items.Item:
    """This method takes as argument the RAW (JSON decoded) response for an openHAB item.

    It checks of what type the item is and returns a class instance of the
    specific item filled with the item's state.

    Args:
      json_data (dict): The JSON decoded data as returned by the openHAB server.

    Returns:
      Item: A corresponding Item class instance with the state of the item.
    """
    type = json_data['type']
    if type == 'Group' and 'groupType' in json_data:
      type = json_data["groupType"]

    if type == 'Switch':
      return openhab.items.SwitchItem(self, json_data)

    if type == 'DateTime':
      return openhab.items.DateTimeItem(self, json_data)

    if type == 'Contact':
      return openhab.items.ContactItem(self, json_data)

    if type.startswith('Number'):
      if type.startswith('Number:'):
        m = re.match(r'''^([^\s]+)''', json_data['state'])

        if m:
          json_data['state'] = m.group(1)

      return openhab.items.NumberItem(self, json_data)

    if type == 'Dimmer':
      return openhab.items.DimmerItem(self, json_data)

    if type == 'Color':
      return openhab.items.ColorItem(self, json_data)

    if type == 'Rollershutter':
      return openhab.items.RollershutterItem(self, json_data)

    if type == 'Player':
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
