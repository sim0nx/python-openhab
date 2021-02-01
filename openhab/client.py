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


from aiohttp_sse_client import client as sse_client
import asyncio
import threading
import requests
import weakref
import json


from requests.auth import HTTPBasicAuth


import openhab.items
import openhab.events
import openhab.types
import openhab.audio

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
    self.all_items:typing.Dict[str,openhab.items.Item] = {}
    self.http_buffersize = 4*1024*1024

    if http_auth is not None:
      self.session.auth = http_auth
    elif not (username is None or password is None):
      self.session.auth = HTTPBasicAuth(username, password)

    self.timeout = timeout
    self.maxEchoToOpenhabMS = max_echo_to_openhab_ms

    self.logger = logging.getLogger(__name__)
    self.sseDaemon = None
    self.__keep_event_daemon_running__ = False
    self.__wait_while_looping = threading.Event()
    self.eventListeners: typing.List[typing.Callable] = []
    if self.autoUpdate:
      self.__installSSEClient__()

  def _check_req_return(self, req: requests.Response) -> None:
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
      self.logger.error("HTTP error: {} caused by request '{}' with content '{}' ".format(req.status_code, req.url, req.content))

      req.raise_for_status()

  def _parse_item(self, event: openhab.events.ItemEvent) -> None:
    """method to parse an ItemEvent from openhab.
        it interprets the received ItemEvent data.
        in case the item was previously registered it will then delegate further parsing of the event to item itself through a call of the items _processExternalEvent method

            Args:
                  event:openhab.events.ItemEvent holding the event data
        """

  def _parse_event(self, event_data: typing.Dict) -> None:
    """method to parse a event from openhab.
    it interprets the received event dictionary and populates an openhab.events.event Object.
    for Item events it then calls _parseItem for a more detailed interpretation of the received data
    then it informs all registered listeners of openhab events
        Args:
              event_data send by openhab in a Dict
    """
    log = logging.getLogger(__name__)

    if "type" in event_data:
      event_reason = event_data["type"]

      if event_reason in ["ItemCommandEvent", "ItemStateEvent", "ItemStateChangedEvent"]:
        item_name = event_data["topic"].split("/")[-2]
        event_data = json.loads(event_data["payload"])

        raw_event = openhab.events.RawItemEvent(item_name=item_name, event_type=event_reason, content=event_data)
        self._inform_event_listeners(raw_event)

        if item_name in self.registered_items:
          item = self.registered_items[item_name]
          if item is None:
            self.logger.warning("item '{}' was removed in all scopes. Ignoring the events coming in for it.".format(item_name))
          else:
            item._process_external_event(raw_event)
        else:
          self.logger.debug("item '{}' not registered. ignoring the arrived event.".format(item_name))

    else:
      log.debug("received unknown Event-data_type in Openhab Event stream: {}".format(event_data))

  def _inform_event_listeners(self, event: openhab.events.RawItemEvent):
    """internal method to send itemevents to listeners.
          Args:
                event:openhab.events.ItemEvent to be sent to listeners
        """
    for aListener in self.eventListeners:
      try:
        aListener(event)
      except Exception as e:
        self.logger.error("error executing Eventlistener for event:{}.".format(event.item_name), e)

  def add_event_listener(self, listener: typing.Callable[[openhab.events.RawItemEvent], None]):
    """method to register a callback function to get informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] a method with one parameter of data_type openhab.events.ItemEvent which will be called for every event
        """
    self.eventListeners.append(listener)

  def remove_event_listener(self, listener: typing.Optional[typing.Callable[[openhab.events.RawItemEvent], None]] = None):
    """method to unregister a callback function to stop getting informed about all Item-Events received from openhab.
          Args:
              listener:typing.Callable[[openhab.events.ItemEvent] the method to be removed.
        """
    if listener is None:
      self.eventListeners.clear()
    elif listener in self.eventListeners:
      self.eventListeners.remove(listener)

  def sse_client_handler(self):
    """the actual handler to receive Events from openhab
            """
    self.logger.info("about to connect to Openhab Events-Stream.")

    async def run_loop():
      async with sse_client.EventSource(self.events_url, read_bufsize=self.http_buffersize) as event_source:
        try:
          self.logger.info("starting Openhab - Event Daemon")
          async for event in event_source:
            if not self.__keep_event_daemon_running__:
              self.sseDaemon = None
              return
            event_data = json.loads(event.data)
            self._parse_event(event_data)

        except ConnectionError as exception:
          self.logger.error("connection error")
          self.logger.exception(exception)
    while self.__keep_event_daemon_running__:
      # keep restarting the handler after timeouts or connection issues
      try:
        asyncio.run(run_loop())
      except asyncio.TimeoutError:
        self.logger.info("reconnecting after timeout")
      except openhab.types.TypeNotImplementedError as e:
        self.logger.warning("received unknown datatye '{}' for item '{}'".format(e.datatype,e.itemname))
      except Exception as e:
        self.logger.exception(e)

    self.sseDaemon = None

  def get_registered_items(self) -> weakref.WeakValueDictionary:
    """get a Dict of weak references to registered items.
            Args:
              an Item object
        """
    return self.registered_items

  def register_all_items(self) -> None:
    """fetches all items from openhab and caches them in all_items.
      subsequent calls to get_item will use this cache.
      subsequent calls to register_all_items will rebuld the chache
    """
    self.all_items = self.fetch_all_items()
    for item in self.all_items.values():
      self.register_item(item)

  def register_item(self, item: openhab.items.Item) -> None:
    """method to register an instantiated item. registered items can receive commands and updates from openhab.
    Usually you don´t need to register as Items register themself.
        Args:
          an Item object
    """
    if item is not None and item.name is not None:
      if item.name not in self.registered_items:
        self.logger.debug("registered item:{}".format(item.name))
        self.registered_items[item.name] = item

  def unregister_item(self,name):
    if name in self.all_items:
      self.all_items.pop(name)

  def stop_receiving_events(self):
    """stop to receive events from openhab.
        """
    self.__keep_event_daemon_running__ = False

  def start_receiving_events(self):
    """start to receive events from openhab.
        """
    if not self.__keep_event_daemon_running__:
      if self.sseDaemon is not None:
        if self.sseDaemon.is_alive():
          # we are running already and did not stop yet.
          # so we simply keep running
          self.__keep_event_daemon_running__ = True
          return
    self.__installSSEClient__()

  def __installSSEClient__(self) -> None:
    """ installs an event Stream to receive all Item events"""

    self.__keep_event_daemon_running__ = True
    self.keep_running = True
    self.sseDaemon = threading.Thread(target=self.sse_client_handler, args=(), daemon=True)

    self.logger.info("about to connect to Openhab Events-Stream.")
    self.sseDaemon.start()

  def stop_looping(self):
    """ method to reactivate the thread which went into the loop_for_events loop.
        """
    self.__wait_while_looping.set()

  def loop_for_events(self):
    """ method to keep waiting for events from openhab
            you can use this method after your program finished initialization and all other work and now wants to keep waiting for events.
    """
    self.__wait_while_looping.wait()

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
    items = {}  # type: dict
    res = self.req_get('/items/')

    for i in res:
      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name: str, force_request_to_openhab:typing.Optional[bool]=False) -> openhab.items.Item:
    """Returns an item with its state and data_type as fetched from openHAB.

    Args:
      name (str): The name of the item to fetch from openHAB.

    Returns:
      Item: A corresponding Item class instance with the state of the requested item.
    """
    if name in self.all_items and not force_request_to_openhab:
      return self.all_items[name]


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

    if _type == 'String':
      return openhab.items.StringItem(self, json_data)

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

  # audio
  def get_audio_defaultsink(self) -> openhab.audio.Audiosink:
    """returns openhabs default audio sink


        Returns:
          openhab.audio.Audiosink: the audio sink
    """
    defaultsink = self._get_audio_defaultsink_raw()
    return openhab.audio.Audiosink.json_to_audiosink(defaultsink,self)

  def _get_audio_defaultsink_raw(self) -> typing.Dict:
    return self.req_get('/audio/defaultsink')

  def get_all_audiosinks(self) -> typing.List[openhab.audio.Audiosink]:
    """returns openhabs audio sinks


            Returns:
              List[openhab.audio.Audiosink]: a list of audio sinks
        """
    result: typing.List[openhab.audio.Audiosink] = []
    sinks = self._get_all_audiosinks_raw()
    for sink in sinks:
      result.append(openhab.audio.Audiosink.json_to_audiosink(sink,self))
    return result

  def _get_all_audiosinks_raw(self) -> typing.Any:
    return self.req_get('/audio/sinks')

  # voices
  def get_audio_defaultvoice(self) -> openhab.audio.Voice:
    """returns openhabs default voice


        Returns:
          openhab.audio.Voice: the voice
    """
    defaultvoice = self._get_audio_defaultvoice_raw()
    return openhab.audio.Voice.json_to_voice(defaultvoice,self)

  def _get_audio_defaultvoice_raw(self) -> typing.Dict:
    return self.req_get('/voice/defaultvoice')

  def get_all_voices(self) -> typing.List[openhab.audio.Voice]:
    """returns openhabs voices


            Returns:
              List[openhab.audio.Voice]: a list of voices
        """
    result: typing.List[openhab.audio.Voice] = []
    voices = self._get_all_voices_raw()
    for voice in voices:
      result.append(openhab.audio.Voice.json_to_voice(voice,self))
    return result

  def _get_all_voices_raw(self) -> typing.Dict:
    return self.req_get('/voice/voices')

  # voiceinterpreters
  def get_voicesinterpreter(self, id:str) -> openhab.audio.Voiceinterpreter:
    """returns a openhab voiceinterpreter
    Args:
      id (str): The id of the voiceinterpreter to be fetched.
    Returns:
      openhab.audio.Voiceinterpreter: the Voiceinterpreter
        """
    voiceinterpreter = self._get_voicesinterpreter_raw(id)
    return openhab.audio.Voiceinterpreter.json_to_voiceinterpreter(voiceinterpreter,self)


  def _get_voicesinterpreter_raw(self, id:str) -> typing.Dict:
    return self.req_get('/voice/interpreters/{}'.format(id))

  def get_all_voicesinterpreters(self) -> typing.List[openhab.audio.Voiceinterpreter]:
    """returns openhabs voiceinterpreters
            Returns:
              List[openhab.audio.Voiceinterpreter]: a list of voiceinterpreters
    """
    result: typing.List[openhab.audio.Voiceinterpreter] = []
    voiceinterpreters = self._get_all_voiceinterpreters_raw()
    for voiceinterpreter in voiceinterpreters:
      result.append(openhab.audio.Voiceinterpreter.json_to_voiceinterpreter(voiceinterpreter,self))
    return result

  def _get_all_voiceinterpreters_raw(self) -> typing.Dict:
    return self.req_get('/voice/interpreters')

  def say(self, text: str, audiosinkid: str, voiceid: str):
    log.info("sending say command to OH for voiceid:'{}', audiosinkid:'{}'".format(voiceid,audiosinkid))
    url=self.base_url + "/voice/say/?voiceid={voiceid}&sinkid={sinkid}".format(voiceid=requests.utils.quote(voiceid), sinkid=requests.utils.quote(audiosinkid))
    r = self.session.post(url, data=text, headers={'Accept': 'application/json'}, timeout=self.timeout)
    self._check_req_return(r)

  def interpret(self, text: str, voiceinterpreterid: str):
    url=self.base_url + "/voice/interpreters/{interpreterid}".format(interpreterid=requests.utils.quote(voiceinterpreterid))
    r = self.session.post(url, data=text, headers={'Accept': 'application/json'}, timeout=self.timeout)
    self._check_req_return(r)



# noinspection PyPep8Naming
class openHAB(OpenHAB):
  """Legacy class wrapper."""

  def __init__(self, *args, **kwargs):
    """Constructor."""
    super().__init__(*args, **kwargs)

    warnings.warn('The use of the "openHAB" class is deprecated, please use "OpenHAB" instead.', DeprecationWarning)
