# -*- coding: utf-8 -*-
"""tests the subscription for events from openhab """

#
# Alexey Grubauer (c) 2020-present <alexey@ingenious-minds.at>
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

import openhab
import openhab.events
import openhab.types
import time
import openhab.items as items
import logging
import random
import testutil
from requests.auth import HTTPBasicAuth


from datetime import datetime

log = logging.getLogger(__name__)
logging.basicConfig(level=10, format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("errormessage")
log.warning("waringingmessage")
log.info("infomessage")
log.debug("debugmessage")


base_url_oh2 = 'http://10.10.20.80:8080/rest'
base_url_oh3 = "http://10.10.20.85:8080/rest"

token = "in openhab admin web interface klick your created user (lower left corner). then create new API toker and copy it here"
token=OPENHAB_AUTH_TOKEN_PRODUCTION

target_oh_version = 3



expected_state = None
state_correct_count = 0
state_count = 0

expected_command = None
command_correct_count = 0

expected_new_state = None
expected_old_state = None
state_changed_correct_count = 0
sleeptime_in_event_listener = 0
count = 0

do_breakpoint = False


if target_oh_version==2:
  headers = {"Authorization": token}
  myopenhab = openhab.OpenHAB(base_url_oh2, openhab_version= openhab.OpenHAB.Version.OH2 ,auto_update=True,http_auth=HTTPBasicAuth(token,""),http_headers_for_autoupdate=headers)
elif target_oh_version==3:
  headers = {"Authorization": "{}".format(token)}
  myopenhab = openhab.OpenHAB(base_url_oh3, openhab_version= openhab.OpenHAB.Version.OH3 , auto_update=True, http_auth=HTTPBasicAuth(token, ""), http_headers_for_autoupdate=headers)
myItemfactory = openhab.items.ItemFactory(myopenhab)

random.seed()
namesuffix = "_{}".format(random.randint(1, 1000))


def on_item_state(item: openhab.items.Item, event: openhab.events.ItemStateEvent):
  global state_correct_count
  log.info("########################### STATE arrived for {itemname} : eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state})".format(
    itemname=event.item_name, eventvalue=event.value, eventvalueraw=event.value_raw, item_state=item._state, itemstate=item.state))
  time.sleep(sleeptime_in_event_listener)
  if expected_state is not None:
    if isinstance(event.value, datetime):
      testutil.doassert(expected_state, event.value.replace(tzinfo=None), "stateEvent item {} ".format(item.name))
    else:
      testutil.doassert(expected_state, event.value, "stateEvent item {} ".format(item.name))
    state_correct_count += 1


def on_item_statechange(item: openhab.items.Item, event: openhab.events.ItemStateChangedEvent):
  global state_changed_correct_count
  log.info("########################### STATE of {itemname} CHANGED from {oldvalue} to {newvalue} (items state: {new_value_item}.".format(itemname=event.item_name, oldvalue=event.old_value, newvalue=event.value, new_value_item=item.state))
  time.sleep(sleeptime_in_event_listener)
  if expected_new_state is not None:
    if isinstance(event.value, datetime):
      testutil.doassert(expected_new_state, event.value.replace(tzinfo=None), "state changed event item {} value".format(item.name))
    else:
      testutil.doassert(expected_new_state, event.value, "state changed event item {} new value".format(item.name))

  if expected_old_state is not None:
    if isinstance(event.old_value, datetime):
      testutil.doassert(expected_old_state, event.old_value.replace(tzinfo=None), "state changed event item {} old value".format(item.name))
    else:
      testutil.doassert(expected_old_state, event.old_value, "OLD state changed event item {} old value".format(item.name))

  state_changed_correct_count += 1


def on_item_command(item: openhab.items.Item, event: openhab.events.ItemCommandEvent):
  global command_correct_count
  log.info("########################### COMMAND arrived for {itemname} : eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state})".format(
    itemname=event.item_name, eventvalue=event.value, eventvalueraw=event.value_raw, item_state=item._state, itemstate=item.state))
  time.sleep(sleeptime_in_event_listener)
  if expected_command is not None:
    if isinstance(event.value, datetime):
      testutil.doassert(expected_command, event.value.replace(tzinfo=None), "command event item {}".format(item.name))
    else:
      testutil.doassert(expected_command, event.value, "command event item {}".format(item.name))
    command_correct_count += 1




def create_event_data(event_type: openhab.events.ItemEventType, itemname, payload):
  if event_type == openhab.events.ItemStateEventType:
    event_type_topic_path = "statechanged"
  elif event_type == openhab.events.ItemStateChangedEventType:
    event_type_topic_path = "state"
  elif event_type == openhab.events.ItemCommandEventType:
    event_type_topic_path = "command"
  else:
    raise NotImplementedError("Event type {} not implemented".format(event_type))
  result = {"type": event_type, "topic": "smarthome/items/{itemname}/{event_type_topic_path}".format(itemname=itemname, event_type_topic_path=event_type_topic_path), "payload": payload}
  return result


def create_event_payload(type: str, value: str, old_type: str = None, old_value: str = None):
  result = '{"type":"' + type + '","value":"' + str(value) + '"'
  if old_type is None:
    old_type = type
  if old_value is not None:
    result = result + ', "oldType":"' + old_type + '","oldValue":"' + str(old_value) + '"'
  result = result + '}'
  return result


def test_number_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.NumberItem = myItemfactory.create_or_update_item(name="test_eventSubscription_numberitem_A{}".format(namesuffix), data_type=openhab.items.NumberItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = 170.3

    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)

    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)

    expected_new_state = expected_state = sending_state = -4
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)

    expected_new_state = expected_state = sending_state = 170.3
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Quantity", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(3, state_correct_count)

    expected_new_state = expected_state = 180
    sending_state = "180 °"
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Quantity", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(4, state_correct_count)

    expected_old_state = 180
    expected_new_state = expected_state = 190
    sending_state = "190 °"
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Quantity", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)

    expected_old_state = 190
    expected_new_state = expected_state = 200
    sending_state = "200 °"
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Quantity", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)

    expected_old_state = None
    expected_command = 200.1
    sending_command = 200.1

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("Quantity", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_state = 123.4
    expected_new_state = expected_state = sending_state
    expected_command = sending_state
    expected_old_state = None

    testitem.state = sending_state
    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    expected_old_state = sending_state
    expected_new_state = expected_state = sending_state = expected_command = 567.8

    testitem.state = sending_state
    time.sleep(0.5)
    testutil.doassert(6, state_correct_count)
    testutil.doassert(4, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    expected_old_state = sending_state
    expected_new_state = expected_state = sending_state = expected_command = 999.99

    testitem.command(sending_state)
    time.sleep(0.5)
    testutil.doassert(7, state_correct_count)
    testutil.doassert(5, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

  finally:
    pass
    testitem.delete()

def test_events_stress():
  created_itemname = "test_eventSubscription_numberitem_A{}".format(namesuffix)
  def on_item_state_stress(item: openhab.items.Item, event: openhab.events.ItemStateEvent):
    global state_correct_count
    global state_count

    log.info("########################### STATE arrived for {itemname} : eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state})".format(
      itemname=event.item_name, eventvalue=event.value, eventvalueraw=event.value_raw, item_state=item._state, itemstate=item.state))
    if item.name == created_itemname:
      state_count += 1
    time.sleep(sleeptime_in_event_listener)
    if expected_state is not None:
      if isinstance(event.value, datetime):
        testutil.doassert(expected_state, event.value.replace(tzinfo=None), "stateEvent item {} ".format(item.name))
      else:
        testutil.doassert(expected_state, event.value, "stateEvent item {} ".format(item.name))
      state_correct_count += 1

  try:
    testitem: openhab.items.NumberItem = myItemfactory.create_or_update_item(name=created_itemname, data_type=openhab.items.NumberItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state_stress, also_get_my_echos_from_openhab=True)
    #testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=False)
    #testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=False)

    expected_state = None
    sleeptime_in_event_listener = 0.5
    state_correct_count = 0
    global state_count
    state_count = 0
    number_of_messages = 30
    for i in range(1,number_of_messages+1):
      log.info("sending state:{}".format(i))
      testitem.state = i
      time.sleep(sleeptime_in_event_listener / 2)

    #
    #
    #
    # sending_state = 123.4
    # expected_new_state = expected_state = sending_state
    # expected_command = sending_state
    # expected_old_state = None
    #
    # testitem.state = sending_state
    time.sleep(((number_of_messages /2)+3)*sleeptime_in_event_listener)
    testutil.doassert(number_of_messages, state_count)

  finally:
    pass
    testitem.delete()

def test_string_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.StringItem = myItemfactory.create_or_update_item(name="test_eventSubscription_stringitem_A{}".format(namesuffix), data_type=openhab.items.StringItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = "test value 1"
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_new_state = expected_state = sending_state = "äöü°"
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = "test value 2"
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("String", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = None
    sending_command = "test value 3"
    expected_new_state = expected_state = sending_command
    expected_command = sending_command

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("String", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_state = "test value 4"
    expected_new_state = expected_state = sending_state
    expected_command = sending_state
    expected_old_state = None

    testitem.state = sending_state
    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    expected_old_state = sending_state
    expected_new_state = expected_state = sending_state = expected_command = "test value 5"
    testitem.command(sending_state)
    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_datetime_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.DateTimeItem = myItemfactory.create_or_update_item(name="test_eventSubscription_datetimeitem_A{}".format(namesuffix), data_type=openhab.items.DateTimeItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    log.info("starting step 1")
    expected_new_state = expected_state = sending_state = datetime.now()
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("DateTime", str(sending_state)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("starting step 2")
    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = datetime.now()
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("DateTime", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("################## starting tests  with real item on openhab")
    log.info("starting step 3")

    sending_state = datetime(2001, 2, 3, 4, 5, 6, microsecond=7000)
    expected_new_state = expected_state = sending_state
    expected_command = sending_state
    expected_old_state = None

    testitem.state = sending_state
    time.sleep(0.5)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("starting step 4")
    expected_new_state = expected_old_state = expected_state
    expected_new_state = expected_command = expected_state = sending_command = datetime(2001, 2, 3, 4, 5, 6, microsecond=8000)
    testitem.command(sending_command)
    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_player_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.PlayerItem = myItemfactory.create_or_update_item(name="test_eventSubscription_playeritem_A{}".format(namesuffix), data_type=openhab.items.PlayerItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = openhab.types.PlayPauseType.PLAY
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("PlayPause", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("PlayPause", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_new_state = expected_state = sending_state = openhab.types.RewindFastforward.FASTFORWARD
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("RewindFastforward", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.PlayPauseType.PAUSE
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("PlayPause", str(sending_state), old_type="RewindFastforward", old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_command = openhab.types.NextPrevious.NEXT
    expected_command = openhab.types.NextPrevious.NEXT

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("NextPrevious", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_command = expected_command = openhab.types.PlayPauseType.PAUSE
    expected_new_state = expected_state = sending_command
    expected_old_state = None
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = expected_state
    sending_command = expected_command = openhab.types.PlayPauseType.PLAY
    expected_new_state = expected_state = sending_command
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(3, command_correct_count)

    expected_old_state = openhab.types.PlayPauseType.PLAY
    sending_command = expected_command = openhab.types.NextPrevious.NEXT
    expected_new_state = expected_state = openhab.types.PlayPauseType.PLAY
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)  # NEXT is not a state!
    testutil.doassert(3, state_changed_correct_count)  # NEXT is not a state!
    testutil.doassert(4, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_switch_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.SwitchItem = myItemfactory.create_or_update_item(name="test_eventSubscription_switchitem_A{}".format(namesuffix), data_type=openhab.items.SwitchItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = openhab.types.OnOffType.ON
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("OnOff", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.OnOffType.OFF
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("OnOff", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_command = sending_command = openhab.types.OnOffType.ON

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("OnOff", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_state = sending_command = expected_command = openhab.types.OnOffType.ON
    expected_new_state = expected_state = sending_command
    expected_old_state = None
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = sending_state
    sending_state = openhab.types.OnOffType.OFF
    expected_new_state = expected_state = sending_state

    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_contact_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.ContactItem = myItemfactory.create_or_update_item(name="test_eventSubscription_contactitem_A{}".format(namesuffix), data_type=openhab.items.ContactItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = openhab.types.OpenCloseType.OPEN
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("OpenClosed", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.OpenCloseType.CLOSED
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("OpenClosed", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_command = sending_command = openhab.types.OpenCloseType.OPEN

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("OpenClosed", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_state = sending_command = expected_command = openhab.types.OpenCloseType.OPEN
    expected_new_state = expected_state = sending_command
    expected_old_state = None
    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    expected_old_state = sending_state
    sending_state = openhab.types.OpenCloseType.CLOSED
    expected_new_state = expected_state = sending_state

    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_dimmer_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.DimmerItem = myItemfactory.create_or_update_item(name="test_eventSubscription_dimmeritem_A{}".format(namesuffix), data_type=openhab.items.DimmerItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = 45.67
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = 12.12
    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Percent", str(sending_state), old_value=expected_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_command = sending_command = 44.44

    event_data = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("Percent", str(sending_command)))
    myopenhab._parse_event(event_data)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    log.info("################## starting tests  with real item on openhab")

    sending_state = sending_command = expected_command = 66.77
    expected_new_state = expected_state = sending_command
    expected_old_state = None
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = sending_state
    sending_state = 99.5
    expected_new_state = expected_state = sending_state

    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = sending_state
    expected_state = sending_state = openhab.types.OnOffType.OFF
    expected_new_state = 0
    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(4, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = 0
    expected_state = sending_state = openhab.types.OnOffType.ON
    expected_new_state = 100
    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)
    testutil.doassert(5, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = 100
    expected_command = sending_command = expected_state = openhab.types.IncreaseDecreaseType.DECREASE
    expected_new_state = 99
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(5, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = 99
    expected_command = sending_command = expected_state = openhab.types.IncreaseDecreaseType.DECREASE
    expected_new_state = 98
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(5, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(4, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_color_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.ColorItem = myItemfactory.create_or_update_item(name="test_eventSubscription_coloritem_A{}".format(namesuffix), data_type=openhab.items.ColorItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = 45.67
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = "1,2,3"
    expected_new_state = expected_state = 1, 2, 3
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("HSB", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = 1, 2, 3
    sending_old_state = "1,2,3"
    expected_new_state = expected_state = 4, 5, 6
    sending_state = "4,5,6"

    event_data = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("HSB", str(sending_state), old_type="HSB", old_value=sending_old_state))
    myopenhab._parse_event(event_data)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("################## starting tests  with real item on openhab")
    expected_new_state = expected_old_state = None
    expected_state = expected_command = sending_command = (1, 2, 3)

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    sending_state = sending_command = expected_command = 66.77
    expected_new_state = 1, 2, 66.77
    expected_state = sending_state
    expected_old_state = 1, 2, 3
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = expected_new_state
    expected_state = sending_state = 99.5
    expected_new_state = 1, 2, 99.5

    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)
    testutil.doassert(4, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    expected_old_state = expected_new_state
    expected_command = sending_command = openhab.types.IncreaseDecreaseType.DECREASE

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(4, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = expected_new_state
    expected_state = openhab.types.OnOffType.OFF
    expected_new_state = 1, 2, 0

    expected_command = sending_command = openhab.types.OnOffType.OFF

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(6, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(5, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(4, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_rollershutter_item():
  global expected_state
  global state_correct_count

  global expected_command
  global command_correct_count

  global expected_new_state
  global expected_old_state
  global state_changed_correct_count

  global do_breakpoint

  state_correct_count = 0
  command_correct_count = 0
  state_changed_correct_count = 0

  try:
    testitem: openhab.items.RollershutterItem = myItemfactory.create_or_update_item(name="test_eventSubscription_rollershutteritem_A{}".format(namesuffix), data_type=openhab.items.RollershutterItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=True)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=True)

    expected_new_state = expected_state = sending_state = 45.67
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = openhab.types.UpDownType.UP
    expected_state = sending_state
    event_data = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("UpDown", str(sending_state)))
    myopenhab._parse_event(event_data)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("################## starting tests  with real item on openhab")
    expected_new_state = expected_old_state = None
    expected_state = expected_command = sending_command = 55.66

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)

    sending_state = sending_command = expected_command = 66.77
    expected_new_state = 66.77
    expected_state = sending_state
    expected_old_state = 55.66
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)

    log.info("xx")
    expected_old_state = expected_new_state
    expected_state = expected_command = sending_command = openhab.types.UpDownType.UP
    expected_new_state = 0
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(3, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = expected_new_state
    expected_state = 0
    expected_new_state = 0

    expected_command = sending_command = openhab.types.StopMoveType.STOP

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)  # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(3, state_changed_correct_count)  # openhab does not automatically increase the value
    testutil.doassert(4, command_correct_count)

  finally:
    pass
    testitem.delete()


def test_echos_for_rollershutter_item():

  global do_breakpoint
  count=0
  try:
    log.info("testing echos for rollershutter")

    def on_item_command(item: openhab.items.Item, event: openhab.events.ItemCommandEvent):
      global count
      count +=1

    def on_item_statechange(item: openhab.items.Item, event: openhab.events.ItemStateChangedEvent):
      global count
      count += 1
    def on_item_state(item: openhab.items.Item, event: openhab.events.ItemStateEvent):
      global count
      count += 1

    testitem: openhab.items.RollershutterItem = myItemfactory.create_or_update_item(name="test_eventSubscription_rollershutteritem_A{}".format(namesuffix), data_type=openhab.items.RollershutterItem)
    testitem.add_event_listener(openhab.events.ItemStateEventType, on_item_state, also_get_my_echos_from_openhab=False)
    testitem.add_event_listener(openhab.events.ItemCommandEventType, on_item_command, also_get_my_echos_from_openhab=False)
    testitem.add_event_listener(openhab.events.ItemStateChangedEventType, on_item_statechange, also_get_my_echos_from_openhab=False)

    testitem.command(75.66)
    testitem.command(75.65)
    testitem.command(75.64)

    time.sleep(0.5)
    testutil.doassert(0, count)

    testitem.command(55.55)
    time.sleep(0.5)
    testutil.doassert(0, count)

    testitem.state = 33.22
    time.sleep(0.5)
    testutil.doassert(0, count)

    testitem.update(11.12)
    time.sleep(0.5)
    testutil.doassert(0, count)

    log.info("########## testing for echos for rollershutter finished seccessfully")

  finally:
    pass
    testitem.delete()


# time.sleep(3)
# log.info("stopping daemon")
# myopenhab.stop_receiving_events()
# log.info("stopped daemon")
# time.sleep(1)
# testitem: openhab.items.RollershutterItem = myItemfactory.create_or_update_item(name="dummy_test_item_{}".format(namesuffix), data_type=openhab.items.RollershutterItem)
# time.sleep(1)
# testitem.delete()
# time.sleep(1)
# log.info("restarting daemon")
# myopenhab.start_receiving_events()
# log.info("restarted daemon")

# test_number_item()
# test_string_item()
# test_datetime_item()
# test_player_item()
# test_switch_item()
# test_contact_item()
# test_dimmer_item()
# test_rollershutter_item()
# test_echos_for_rollershutter_item()
test_events_stress()
log.info("tests for events finished successfully")

myopenhab.loop_for_events()
log.info("stopping program")
