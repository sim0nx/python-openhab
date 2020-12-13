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
from __future__ import annotations
from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable


import openhab
import openhab.events
import time
import openhab.items as items
import logging
import json
import random
import tests.testutil as testutil
log=logging.getLogger()
logging.basicConfig(level=10,format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("errormessage")
log.warning("waringingmessage")
log.info("infomessage")
log.debug("debugmessage")



base_url = 'http://10.10.20.81:8080/rest'



testdata:Dict[str,Tuple[str,str,str]]={'OnOff'           : ('ItemCommandEvent','testroom1_LampOnOff','{"type":"OnOff","value":"ON"}'),
                                   'Decimal'         : ('ItemCommandEvent','xx','{"type":"Decimal","value":"170.0"}'),
                                   'DateTime'        : ('ItemCommandEvent','xx','{"type":"DateTime","value":"2020-12-04T15:53:33.968+0100"}'),
                                   'UnDef'           : ('ItemCommandEvent','xx','{"type":"UnDef","value":"UNDEF"}'),
                                   'String'          : ('ItemCommandEvent','xx','{"type":"String","value":"WANING_GIBBOUS"}'),
                                   'Quantitykm'      : ('ItemCommandEvent','xx','{"type":"Quantity","value":"389073.99674024084 km"}'),
                                   'Quantitykm grad' : ('ItemCommandEvent','xx', '{"type":"Quantity","value":"233.32567712620255 °"}'),
                                   'Quantitywm2'     : ('ItemCommandEvent','xx', '{"type":"Quantity","value":"0.0 W/m²"}'),
                                   'Percent'         : ('ItemCommandEvent','xx', '{"type":"Percent","value":"52"}'),
                                   'UpDown'          : ('ItemCommandEvent','xx', '{"type":"UpDown","value":"DOWN"}'),


                                   'OnOffChange'                   : ('ItemStateChangedEvent','xx', '{"type":"OnOff","value":"OFF","oldType":"OnOff","oldValueRaw":"ON"}'),
                                   'DecimalChange'                 : ('ItemStateChangedEvent','xx', '{"type":"Decimal","value":"170.0","oldType":"Decimal","oldValueRaw":"186.0"}'),
                                   'QuantityChange'                : ('ItemStateChangedEvent','xx', '{"type":"Quantity","value":"389073.99674024084 km","oldType":"Quantity","oldValueRaw":"389076.56223012594 km"}'),
                                   'QuantityGradChange'            : ('ItemStateChangedEvent','xx', '{"type":"Quantity","value":"233.32567712620255 °","oldType":"Quantity","oldValueRaw":"233.1365666436372 °"}'),
                                   'DecimalChangeFromNull'         : ('ItemStateChangedEvent','xx', '{"type":"Decimal","value":"0.5","oldType":"UnDef","oldValueRaw":"NULL"}'),
                                   'DecimalChangeFromNullToUNDEF'  : ('ItemStateChangedEvent','xx', '{"type":"Decimal","value":"15","oldType":"UnDef","oldValueRaw":"NULL"}'),
                                   'PercentChange'                 : ('ItemStateChangedEvent','xx', '{"type":"Percent","value":"52","oldType":"UnDef","oldValueRaw":"NULL"}'),


                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   'Datatypechange'                : ('ItemStateChangedEvent','xx', '{"type":"OnOff","value":"ON","oldType":"UnDef","oldValueRaw":"NULL"}')
                                   }
testitems:Dict[str,openhab.items.Item] = {}

def executeParseCheck():
    log.info("executing parse checks")
    for testkey in testdata:
        log.info("testing:{}".format(testkey))
        stringToParse=testdata[testkey]
    log.info("parse checks finished successfully")













if True:
    myopenhab = openhab.OpenHAB(base_url,autoUpdate=True)
    myItemfactory = openhab.items.ItemFactory(myopenhab)
    random.seed()
    namesuffix = "_{}".format(random.randint(1, 1000))
    testnumberA:openhab.items.NumberItem = myItemfactory.createOrUpdateItem(name="test_eventSubscription_numberitem_A{}".format(namesuffix),type=openhab.items.NumberItem)
    testnumberB:openhab.items.NumberItem = myItemfactory.createOrUpdateItem(name="test_eventSubscription_numberitem_B{}".format(namesuffix),type=openhab.items.NumberItem)
    itemname = "test_eventSubscription_switchitem_A{}".format(namesuffix)
    switchItem:openhab.items.SwitchItem = myItemfactory.createOrUpdateItem(name=itemname, type=openhab.items.SwitchItem)
    try:
        testnumberA.state = 44.0
        testnumberB.state = 66.0


        expect_A = None
        expect_B = None


        def on_A_Change(item:openhab.items.NumberItem ,event:openhab.events.ItemStateEvent):
            log.info("########################### UPDATE of {itemname} to eventvalue:{eventvalue}(event value raraw:{eventvalueraw}) (itemstate:{itemstate},item_state:{item_state}) from OPENHAB ONLY".format(
                itemname=event.itemname,eventvalue=event.newValue,eventvalueraw=event.newValueRaw, item_state=item._state,itemstate=item.state))

        testnumberA.addEventListener(openhab.events.ItemCommandEventType,on_A_Change,onlyIfEventsourceIsOpenhab=True)

        def ontestnumberBChange(item:openhab.items.NumberItem ,event:openhab.events.ItemStateEvent):
            log.info("########################### UPDATE of {} to {} (itemsvalue:{}) from OPENHAB ONLY".format(event.itemname, event.newValueRaw, item.state))
            if not expect_B is None:
                assert item.state == expect_B

        testnumberB.addEventListener(openhab.events.ItemCommandEventType,ontestnumberBChange,onlyIfEventsourceIsOpenhab=True)


        def ontestnumberAChangeAll(item:openhab.items.Item ,event:openhab.events.ItemStateEvent):
            if event.source == openhab.events.EventSourceInternal:
                log.info("########################### INTERNAL UPDATE of {} to {} (itemsvalue:{}) from internal".format(event.itemname,event.newValueRaw, item.state))
            else:
                log.info("########################### EXTERNAL UPDATE of {} to {} (itemsvalue:{}) from OPENHAB".format(event.itemname, event.newValueRaw, item.state))

        testnumberA.addEventListener(openhab.events.ItemCommandEventType,ontestnumberAChangeAll,onlyIfEventsourceIsOpenhab=False)

        #print(itemClock)

        time.sleep(2)
        log.info("###################################### starting test 'internal Event'")

        expect_B=2
        testnumberB.state=2
        time.sleep(0.1)

        expect_B = None
        checkcount = 0



        def createEventData(type,itemname,payload):
            result={}
            result["type"]=type
            result["topic"]="smarthome/items/{itemname}/state".format(itemname=itemname)
            result["payload"]=payload
            return result


        def onLight_switchCommand(item: openhab.items.Item, event: openhab.events.ItemCommandEvent):
            log.info("########################### COMMAND of {} to {} (itemsvalue:{}) from OPENHAB".format(event.itemname, event.newValueRaw, item.state))

        def onAnyItemCommand(item: openhab.items.Item, event: openhab.events.ItemStateEvent):
            log.info("########################### UPDATE of {} to {} (itemsvalue:{}) from OPENHAB ONLY".format(event.itemname, event.newValueRaw, item.state))
            if not expected_switch_Value is None:
                global checkcount
                actualValue=event.newValue
                assert actualValue == expected_switch_Value, "expected value to be {}, but it was {}".format(expected_switch_Value, actualValue)
                checkcount+=1



        testname="OnOff"
        expected_switch_Value= "ON"
        type='ItemCommandEvent'

        payload='{"type":"OnOff","value":"ON"}'
        eventData=createEventData(type,itemname,payload)



        switchItem.addEventListener(listeningTypes=openhab.events.ItemCommandEventType,listener=onAnyItemCommand,onlyIfEventsourceIsOpenhab=False)
        switchItem.addEventListener(listeningTypes=openhab.events.ItemCommandEventType, listener=onLight_switchCommand, onlyIfEventsourceIsOpenhab=False)

        myopenhab._parseEvent(eventData)

        expected_switch_Value = "OFF"
        switchItem.off()

        expected_switch_Value = "ON"
        switchItem.on()

        assert checkcount==3, "not all events got processed successfully"



        log.info("###################################### test 'internal Event' finished successfully")



    finally:
        testnumberA.delete()
        testnumberB.delete()
        switchItem.delete()












    keep_going=True
    while keep_going:
        #waiting for events from openhab
        time.sleep(10)

