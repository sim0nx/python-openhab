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
from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable
import openhab
import openhab.events
import openhab.types
import time
import openhab.items as items
import logging
import random
import testutil

from datetime import datetime,timezone
import pytz

log = logging.getLogger()
logging.basicConfig(level=10, format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("errormessage")
log.warning("waringingmessage")
log.info("infomessage")
log.debug("debugmessage")

base_url = 'http://10.10.20.81:8080/rest'

testdata: Dict[str, Tuple[str, str, str]] = {'OnOff': ('ItemCommandEvent', 'testroom1_LampOnOff', '{"type":"OnOff","value":"ON"}'),
                                             'Decimal': ('ItemCommandEvent', 'xx', '{"type":"Decimal","value":"170.0"}'),
                                             'DateTime': ('ItemCommandEvent', 'xx', '{"type":"DateTime","value":"2020-12-04T15:53:33.968+0100"}'),
                                             'UnDef': ('ItemCommandEvent', 'xx', '{"type":"UnDef","value":"UNDEF"}'),
                                             'String': ('ItemCommandEvent', 'xx', '{"type":"String","value":"WANING_GIBBOUS"}'),
                                             'Quantitykm': ('ItemCommandEvent', 'xx', '{"type":"Quantity","value":"389073.99674024084 km"}'),
                                             'Quantitykm grad': ('ItemCommandEvent', 'xx', '{"type":"Quantity","value":"233.32567712620255 °"}'),
                                             'Quantitywm2': ('ItemCommandEvent', 'xx', '{"type":"Quantity","value":"0.0 W/m²"}'),
                                             'Percent': ('ItemCommandEvent', 'xx', '{"type":"Percent","value":"52"}'),
                                             'UpDown': ('ItemCommandEvent', 'xx', '{"type":"UpDown","value":"DOWN"}'),
                                             'OnOffChange': ('ItemStateChangedEvent', 'xx', '{"type":"OnOff","value":"OFF","oldType":"OnOff","old_value_raw":"ON"}'),
                                             'DecimalChange': ('ItemStateChangedEvent', 'xx', '{"type":"Decimal","value":"170.0","oldType":"Decimal","old_value_raw":"186.0"}'),
                                             'QuantityChange': ('ItemStateChangedEvent', 'xx', '{"type":"Quantity","value":"389073.99674024084 km","oldType":"Quantity","old_value_raw":"389076.56223012594 km"}'),
                                             'QuantityGradChange': ('ItemStateChangedEvent', 'xx', '{"type":"Quantity","value":"233.32567712620255 °","oldType":"Quantity","old_value_raw":"233.1365666436372 °"}'),
                                             'DecimalChangeFromNull': ('ItemStateChangedEvent', 'xx', '{"type":"Decimal","value":"0.5","oldType":"UnDef","old_value_raw":"NULL"}'),
                                             'DecimalChangeFromNullToUNDEF': ('ItemStateChangedEvent', 'xx', '{"type":"Decimal","value":"15","oldType":"UnDef","old_value_raw":"NULL"}'),
                                             'PercentChange': ('ItemStateChangedEvent', 'xx', '{"type":"Percent","value":"52","oldType":"UnDef","old_value_raw":"NULL"}'),
                                             'Datatypechange': ('ItemStateChangedEvent', 'xx', '{"type":"OnOff","value":"ON","oldType":"UnDef","old_value_raw":"NULL"}')
                                             }
testitems: Dict[str, openhab.items.Item] = {}




expected_state = None
state_correct_count=0

expected_command = None
command_correct_count=0

expected_new_state = None
expected_old_state = None
state_changed_correct_count=0

do_breakpoint=False

def on_item_state(item: openhab.items.Item, event: openhab.events.ItemStateEvent):
  global  state_correct_count
  log.info("########################### STATE arrived for {itemname} : eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state})".format(
    itemname=event.item_name, eventvalue=event.value, eventvalueraw=event.value_raw, item_state=item._state, itemstate=item.state))
  if expected_state is not None:
    if isinstance(event.value,datetime):
      testutil.doassert(expected_state, event.value.replace(tzinfo=None), "stateEvent item {} ".format(item.name))
    else:
      testutil.doassert(expected_state,event.value,"stateEvent item {} ".format(item.name))
    state_correct_count += 1


def on_item_statechange(item: openhab.items.Item, event: openhab.events.ItemStateChangedEvent):
  global state_changed_correct_count
  log.info("########################### STATE of {itemname} CHANGED from {oldvalue} to {newvalue} (items state: {new_value_item}.".format(itemname=event.item_name,oldvalue=event.old_value,newvalue=event.value, new_value_item=item.state))
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

  state_changed_correct_count +=1



def on_item_command(item: openhab.items.Item, event: openhab.events.ItemCommandEvent):
  global command_correct_count
  log.info("########################### COMMAND arrived for {itemname} : eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state})".format(
    itemname=event.item_name, eventvalue=event.value, eventvalueraw=event.value_raw, item_state=item._state, itemstate=item.state))
  if expected_command is not None:
    if isinstance(event.value, datetime):
      testutil.doassert(expected_command, event.value.replace(tzinfo=None), "command event item {}".format(item.name))
    else:
      testutil.doassert(expected_command, event.value, "command event item {}".format(item.name))
    command_correct_count +=1



myopenhab = openhab.OpenHAB(base_url, auto_update=True)
myItemfactory = openhab.items.ItemFactory(myopenhab)

random.seed()
namesuffix = "_{}".format(random.randint(1, 1000))

test_azimuth=myItemfactory.get_item("testworld_Azimuth")
test_azimuth.add_event_listener(listening_types=openhab.events.ItemStateEventType, listener=on_item_state)
test_azimuth.add_event_listener(listening_types=openhab.events.ItemCommandEventType, listener=on_item_command)
test_azimuth.add_event_listener(listening_types=openhab.events.ItemStateChangedEventType, listener=on_item_statechange)






def create_event_data(event_type:openhab.events.ItemEventType, itemname, payload):
  result= {}
  if event_type== openhab.events.ItemStateEventType:
    event_type_topic_path="statechanged"
  elif event_type== openhab.events.ItemStateChangedEventType:
    event_type_topic_path="state"
  elif event_type== openhab.events.ItemCommandEventType:
    event_type_topic_path="command"
  result = {"type": event_type, "topic": "smarthome/items/{itemname}/{event_type_topic_path}".format(itemname=itemname,event_type_topic_path=event_type_topic_path), "payload": payload}
  return result

def create_event_payload(type:str,value:str,oldType:str=None,oldValue:str=None):
  result='{"type":"'+type+'","value":"'+str(value)+'"'
  if oldType is None:
    oldType = type
  if oldValue is not None:
    result = result + ', "oldType":"'+oldType+'","oldValue":"'+str(oldValue)+'"'
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
    #eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, '{"type":"Decimal","value":"'+str(sending_state)+'"}')
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal",str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(1,state_correct_count)


    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal",str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)

    expected_new_state = expected_state = sending_state = -4
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Decimal",str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(2, state_correct_count)

    expected_new_state = expected_state = sending_state = 170.3
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Quantity",str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(3, state_correct_count)

    expected_new_state = expected_state = 180
    sending_state = "180 °"
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Quantity",str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(4, state_correct_count)

    expected_old_state = 180
    expected_new_state = expected_state = 190
    sending_state = "190 °"
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Quantity",str(sending_state),oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)

    expected_old_state = 190
    expected_new_state = expected_state = 200
    sending_state = "200 °"
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Quantity",str(sending_state),oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)

    expected_old_state = None
    expected_command = 200.1
    sending_command = 200.1

    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("Quantity", str(sending_command)))
    myopenhab._parse_event(eventData)
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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)




    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_new_state = expected_state = sending_state = "äöü°"
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("String", str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = "test value 2"
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("String", str(sending_state), oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    expected_old_state = None
    sending_command = "test value 3"
    expected_new_state = expected_state = sending_command
    expected_command = sending_command

    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("String", str(sending_command)))
    myopenhab._parse_event(eventData)
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

def test_dateTime_item():
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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("DateTime", str(sending_state)))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("starting step 2")
    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = datetime.now()
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("DateTime", str(sending_state), oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    log.info("################## starting tests  with real item on openhab")
    log.info("starting step 3")

    sending_state = datetime(2001,2,3,4,5,6,microsecond=7000)
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
    expected_new_state = expected_command = expected_state = sending_state = sending_command = sending_state = datetime(2001,2,3,4,5,6,microsecond=8000)
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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("PlayPause", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    sending_state = openhab.types.UndefType.UNDEF
    expected_new_state = expected_state = None
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("PlayPause", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_new_state = expected_state = sending_state = openhab.types.RewindFastforward.FASTFORWARD
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("RewindFastforward", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.PlayPauseType.PAUSE
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("PlayPause", str(sending_state), oldType="RewindFastforward" ,oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)





    sending_command = openhab.types.NextPrevious.NEXT
    expected_command = openhab.types.NextPrevious.NEXT

    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("NextPrevious", str(sending_command)))
    myopenhab._parse_event(eventData)
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
    testutil.doassert(4, state_correct_count) # NEXT is not a state!
    testutil.doassert(3, state_changed_correct_count) # NEXT is not a state!
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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("OnOff", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.OnOffType.OFF
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("OnOff", str(sending_state), oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)





    expected_command = sending_command = openhab.types.OnOffType.ON


    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("OnOff", str(sending_command)))
    myopenhab._parse_event(eventData)
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

    testitem.state =sending_state

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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("OpenClosed", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = openhab.types.OpenCloseType.CLOSED
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("OpenClosed", str(sending_state), oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)





    expected_command = sending_command = openhab.types.OpenCloseType.OPEN


    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("OpenClosed", str(sending_command)))
    myopenhab._parse_event(eventData)
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

    testitem.state =sending_state

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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = expected_state
    expected_new_state = expected_state = sending_state = 12.12
    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("Percent", str(sending_state), oldValue=expected_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(1, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)





    expected_command = sending_command = 44.44


    eventData = create_event_data(openhab.events.ItemCommandEventType, testitem.name, create_event_payload("Percent", str(sending_command)))
    myopenhab._parse_event(eventData)
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

    testitem.state =sending_state

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)



    expected_old_state = sending_state
    expected_state= sending_state = openhab.types.OnOffType.OFF
    expected_new_state = 0
    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(4, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)



    expected_old_state = 0
    expected_state= sending_state = openhab.types.OnOffType.ON
    expected_new_state = 100
    testitem.state = sending_state

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)
    testutil.doassert(5, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)



    expected_old_state = 100
    expected_command = sending_command = expected_state = sending_state = openhab.types.IncreaseDecreaseType.DECREASE
    expected_new_state = 99
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count) # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(5, state_changed_correct_count) # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = 99
    expected_command = sending_command = expected_state = sending_state = openhab.types.IncreaseDecreaseType.DECREASE
    expected_new_state = 98
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count) # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(5, state_changed_correct_count) # openhab does not automatically increase the value
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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = "1,2,3"
    expected_new_state = expected_state = 1,2,3
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("HSB", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)



    expected_old_state = 1,2,3
    sending_old_state = "1,2,3"
    expected_new_state = expected_state = 4,5,6
    sending_state = "4,5,6"

    eventData = create_event_data(openhab.events.ItemStateChangedEventType, testitem.name, create_event_payload("HSB", str(sending_state), oldType="HSB",oldValue=sending_old_state))
    myopenhab._parse_event(eventData)
    testutil.doassert(2, state_correct_count)
    testutil.doassert(1, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)


    log.info("################## starting tests  with real item on openhab")
    expected_new_state = expected_old_state = None
    expected_state = expected_command = sending_command =  (1,2,3)

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(3, state_correct_count)
    testutil.doassert(2, state_changed_correct_count)
    testutil.doassert(1, command_correct_count)


    sending_state = sending_command = expected_command = 66.77
    expected_new_state = 1,2,66.77
    expected_state = sending_state
    expected_old_state = 1,2,3
    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(4, state_correct_count)
    testutil.doassert(3, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)



    expected_old_state = expected_new_state
    expected_state = sending_state = 99.5
    expected_new_state = 1,2,99.5

    testitem.state =sending_state

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count)
    testutil.doassert(4, state_changed_correct_count)
    testutil.doassert(2, command_correct_count)


    expected_old_state = expected_new_state
    expected_command = sending_command = openhab.types.IncreaseDecreaseType.DECREASE

    testitem.command(sending_command)

    time.sleep(0.5)
    testutil.doassert(5, state_correct_count) # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(4, state_changed_correct_count) # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = expected_new_state
    expected_state =  openhab.types.OnOffType.OFF
    expected_new_state = 1,2,0


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
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("Percent", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(1, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)

    sending_state = openhab.types.UpDownType.UP
    expected_state = sending_state
    eventData = create_event_data(openhab.events.ItemStateEventType, testitem.name, create_event_payload("UpDown", str(sending_state)))
    myopenhab._parse_event(eventData)

    testutil.doassert(2, state_correct_count)
    testutil.doassert(0, state_changed_correct_count)
    testutil.doassert(0, command_correct_count)


    log.info("################## starting tests  with real item on openhab")
    expected_new_state = expected_old_state = None
    expected_state = expected_command = sending_command =  55.66

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
    testutil.doassert(5, state_correct_count) # openhab.types.IncreaseDecreaseType.DECREASE is not sent as state
    testutil.doassert(3, state_changed_correct_count) # openhab does not automatically increase the value
    testutil.doassert(3, command_correct_count)

    expected_old_state = expected_new_state
    expected_state =  0
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


test_number_item()
test_string_item()
test_dateTime_item()
test_player_item()
test_switch_item()
test_contact_item()
test_dimmer_item()
test_rollershutter_item()


keep_going = True
log.info("###################################### tests finished successfully")
while keep_going:
    # waiting for events from openhab
    time.sleep(10)


