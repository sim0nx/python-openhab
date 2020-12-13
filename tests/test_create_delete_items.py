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
from datetime import datetime,timedelta
log=logging.getLogger()
logging.basicConfig(level=10,format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("xx")
log.warning("www")
log.info("iii")
log.debug("ddddd")



base_url = 'http://10.10.20.81:8080/rest'





def testCreateItems(myopenhab:openhab.OpenHAB):
    myitemFactory = openhab.items.ItemFactory(myopenhab)
    random.seed()
    nameprefix = "x2_{}".format(random.randint(1, 1000))
    knxshuttergroup=myopenhab.get_item("gKNXImport_shutter")
    log.info("knxshuttergroup:{}".format(knxshuttergroup))

    aGroupItem:openhab.items.Item =testGroup(myitemFactory,nameprefix)
    log.info("the new group:{}".format(aGroupItem))
    aNumberItem=testNumberItem(myitemFactory,nameprefix)

    aContactItem:openhab.items.ContactItem=testContactItem(myitemFactory,nameprefix)
    log.info("the new aContactItem:{}".format(aContactItem))

    aDatetimeItem:openhab.items.DateTimeItem=testDateTimeItem(myitemFactory,nameprefix)
    log.info("the new aDatetimeItem:{}".format(aDatetimeItem))

    aRollershutterItem:openhab.items.RollershutterItem = testRollershutterItem(myitemFactory, nameprefix)
    log.info("the new aRollershutterItem:{}".format(aRollershutterItem))

    aColorItem:openhab.items.ColorItem = testColorItem(myitemFactory, nameprefix)
    log.info("the new aColorItem:{}".format(aColorItem))

    aDimmerItem:openhab.items.DimmerItem = testDimmerItem(myitemFactory, nameprefix)
    log.info("the new aDimmerItem:{}".format(aDimmerItem))

    aSwitchItem:openhab.items.SwitchItem = testSwitchItem(myitemFactory, nameprefix)
    log.info("the new Switch:{}".format(aSwitchItem))

    aPlayerItem:openhab.items.PlayerItem = testPlayerItem(myitemFactory, nameprefix)
    log.info("the new Player:{}".format(aPlayerItem))

    coloritemname=aColorItem.name
    aColorItem.delete()
    try:
        shouldNotWork=myitemFactory.getItem(coloritemname)
        testutil.doassert(False,True,"this lookup should raise a exception because the item should have been removed.")
    except:
        pass


    #Group, Number, Contact, DateTime, Rollershutter, Color, Dimmer, Switch, Player

def testNumberItem(itemFactory,nameprefix):

    itemname = "{}CreateItemTest".format(nameprefix)
    itemQuantityType = "Angle"  # "Length",Temperature,,Pressure,Speed,Intensity,Dimensionless,Angle
    itemtype = "Number"
    itemtype = openhab.items.NumberItem

    labeltext = "das ist eine testzahl:"
    itemlabel = "[{labeltext}%.1f °]".format(labeltext=labeltext)
    itemcategory = "{}TestCategory".format(nameprefix)
    itemtags: List[str] = ["{}testtag1".format(nameprefix), "{}testtag2".format(nameprefix)]
    itemgroupNames: List[str] = ["{}testgroup1".format(nameprefix), "{}testgroup2".format(nameprefix)]
    grouptype = "{}testgrouptype".format(nameprefix)
    functionname = "{}testfunctionname".format(nameprefix)
    functionparams: List[str] = ["{}testfunctionnameParam1".format(nameprefix), "{}testfunctionnameParam2".format(nameprefix), "{}testfunctionnameParam3".format(nameprefix)]

    x2=itemFactory.createOrUpdateItem(name=itemname, type=itemtype, quantityType=itemQuantityType, label=itemlabel, category=itemcategory, tags=itemtags, groupNames=itemgroupNames, grouptype=grouptype, functionname=functionname, functionparams=functionparams)
    x2.state=123.45
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert(itemtype.TYPENAME+":"+itemQuantityType, x2.type_, "type")
    testutil.doassert(123.45, x2.state, "state")
    testutil.doassert(itemQuantityType, x2.quantityType, "quantityType")
    testutil.doassert(itemlabel, x2.label, "label")
    testutil.doassert(itemcategory,x2.category,"category")
    for aExpectedTag in itemtags:
        testutil.doassert(aExpectedTag in x2.tags,True,"tag {}".format(aExpectedTag))

    for aExpectedGroupname in itemgroupNames:
        testutil.doassert(aExpectedGroupname in x2.groupNames   ,True,"tag {}".format(aExpectedGroupname))

    return x2

def testGroup(itemFactory,nameprefix)->openhab.items.Item:
    itemtype = "Group"
    itemname = "{}TestGroup".format(nameprefix)
    testgroupItem = itemFactory.createOrUpdateItem(name=itemname, type=itemtype)
    return  testgroupItem

def testContactItem(itemFactory,nameprefix):

    itemname = "{}CreateContactItemTest".format(nameprefix)
    itemtype = openhab.items.ContactItem

    x2=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)
    x2.state="OPEN"
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert("OPEN", x2.state, "itemstate")
    x2.state = "CLOSED"
    testutil.doassert("CLOSED", x2.state, "itemstate")
    try:
        x2.state = "SEPP"
        testutil.doassert(False, True, "this should have caused a exception!")
    except:
        pass

    return x2

def testDateTimeItem(itemFactory,nameprefix):

    itemname = "{}CreateDateTimeItemTest".format(nameprefix)
    itemtype = openhab.items.DateTimeItem

    x2=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)
    log.info("current datetime in item:{}".format(x2.state))
    now=datetime.now()
    x2.state=now
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert(now, x2.state, "itemstate")
    return x2

def testRollershutterItem(itemFactory,nameprefix):

    itemname = "{}CreateRollershutterItemTest".format(nameprefix)
    itemtype = openhab.items.RollershutterItem

    x2:openhab.items.RollershutterItem=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)


    x2.up()
    testutil.doassert(itemname,x2.name,"itemname")

    testutil.doassert("UP", x2.state, "itemstate")
    x2.state=53
    testutil.doassert(53, x2.state, "itemstate")
    return x2

def testColorItem(itemFactory,nameprefix):

    itemname = "{}CreateColorItemTest".format(nameprefix)
    itemtype = openhab.items.ColorItem

    x2:openhab.items.ColorItem=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)


    x2.on()
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert("ON", x2.state, "itemstate")
    newValue="51,52,53"
    x2.state=newValue

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(newValue, x2.state, "itemstate")
    return x2



def testDimmerItem(itemFactory,nameprefix):

    itemname = "{}CreateDimmerItemTest".format(nameprefix)
    itemtype = openhab.items.DimmerItem

    x2:openhab.items.DimmerItem=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)


    x2.on()
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert("ON", x2.state, "itemstate")

    x2.off()
    testutil.doassert("OFF", x2.state, "itemstate")


    newValue=51
    x2.state=newValue

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(newValue, x2.state, "itemstate")
    return x2



def testSwitchItem(itemFactory,nameprefix):

    itemname = "{}CreateSwitchItemTest".format(nameprefix)
    itemtype = openhab.items.SwitchItem

    x2:openhab.items.SwitchItem=itemFactory.createOrUpdateItem(name=itemname, type=itemtype)


    x2.on()
    testutil.doassert(itemname,x2.name,"itemname")
    testutil.doassert("ON", x2.state, "itemstate")

    x2.off()
    testutil.doassert("OFF", x2.state, "itemstate")

    x2.toggle()
    testutil.doassert("ON", x2.state, "itemstate")

    newValue = "OFF"
    x2.state = newValue

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(newValue, x2.state, "itemstate")
    return x2




def testPlayerItem(itemFactory,nameprefix):
    itemname = "{}CreatePlayerItemTest".format(nameprefix)
    itemtype = openhab.items.PlayerItem

    x2: openhab.items.PlayerItem = itemFactory.createOrUpdateItem(name=itemname, type=itemtype)
    x2.play()

    testutil.doassert(itemname, x2.name, "itemname")
    testutil.doassert("PLAY", x2.state, "itemstate")

    x2.pause()
    testutil.doassert("PAUSE", x2.state, "itemstate")
    return x2







myopenhab = openhab.OpenHAB(base_url,autoUpdate=False)
keeprunning=True
testCreateItems(myopenhab)


while keeprunning:
    time.sleep(10)

    x=0

