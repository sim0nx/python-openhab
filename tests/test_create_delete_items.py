# -*- coding: utf-8 -*-
"""tests for creating and deletion of items """

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
from datetime import datetime

log = logging.getLogger()
logging.basicConfig(level=10, format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("xx")
log.warning("www")
log.info("iii")
log.debug("ddddd")

base_url = 'http://10.10.20.81:8080/rest'


def test_create_and_delete_items(myopenhab: openhab.OpenHAB, nameprefix):
    log.info("starting tests 'create and delete items'")

    my_item_factory = openhab.items.ItemFactory(myopenhab)
    a_group_item = None
    a_string_item = None
    a_number_item = None
    a_contact_item = None
    a_datetime_item = None
    a_rollershutter_item = None
    a_color_item = None
    a_dimmer_item = None
    a_switch_item = None
    a_player_item = None
    try:
        a_group_item: openhab.items.Item = testGroup(my_item_factory, nameprefix)
        log.info("the new group:{}".format(a_group_item))

        a_string_item: openhab.items.Item = test_StringItem(my_item_factory, nameprefix)
        log.info("the new stringItem:{}".format(a_string_item))

        a_number_item = test_NumberItem(my_item_factory, nameprefix)

        a_contact_item: openhab.items.ContactItem = test_ContactItem(my_item_factory, nameprefix)
        log.info("the new aContactItem:{}".format(a_contact_item))

        a_datetime_item: openhab.items.DateTimeItem = test_DateTimeItem(my_item_factory, nameprefix)
        log.info("the new aDatetimeItem:{}".format(a_datetime_item))

        a_rollershutter_item: openhab.items.RollershutterItem = test_RollershutterItem(my_item_factory, nameprefix)
        log.info("the new aRollershutterItem:{}".format(a_rollershutter_item))

        a_color_item: openhab.items.ColorItem = test_ColorItem(my_item_factory, nameprefix)
        log.info("the new aColorItem:{}".format(a_color_item))

        a_dimmer_item: openhab.items.DimmerItem = test_DimmerItem(my_item_factory, nameprefix)
        log.info("the new aDimmerItem:{}".format(a_dimmer_item))

        a_switch_item: openhab.items.SwitchItem = test_SwitchItem(my_item_factory, nameprefix)
        log.info("the new Switch:{}".format(a_switch_item))

        a_player_item: openhab.items.PlayerItem = test_PlayerItem(my_item_factory, nameprefix)
        log.info("the new Player:{}".format(a_player_item))

        log.info("creation tests worked")
    finally:
        if a_group_item is not None:
          a_group_item.delete()
        if a_string_item is not None:
          a_string_item.delete()
        if a_number_item is not None:
          a_number_item.delete()
        if a_contact_item is not None:
          a_contact_item.delete()
        if a_datetime_item is not None:
          a_datetime_item.delete()
        if a_rollershutter_item is not None:
          a_rollershutter_item.delete()

        if a_color_item is not None:
          coloritemname = a_color_item.name
          a_color_item.delete()
          try:
              should_not_work = my_item_factory.get_item(coloritemname)
              testutil.doassert(False, True, "this getItem should raise a exception because the item should have been removed.")
          except:
              pass
        if a_dimmer_item is not None:
            a_dimmer_item.delete()
        if a_switch_item is not None:
            a_switch_item.delete()
        if a_player_item is not None:
            a_player_item.delete()

    log.info("test 'create and delete items' finished successfully")


def delete_all_items_starting_with(myopenhab: openhab.OpenHAB, nameprefix):
    log.info("starting to delete all items starting with '{}'".format(nameprefix))
    if nameprefix is None:
        return
    if len(nameprefix) < 3:
        log.warning("don´t think that you really want to do this")
        return
    all_items = myopenhab.fetch_all_items()
    count = 0
    for aItemname in all_items:
        if aItemname.startswith(nameprefix):
            a_item = all_items[aItemname]
            a_item.delete()
            count += 1
    log.info("finished to delete all items starting with '{}'. deleted {} items".format(nameprefix, count))


def test_NumberItem(item_factory, nameprefix):
    itemname = "{}CreateItemTest".format(nameprefix)
    item_quantity_type = "Angle"  # "Length",Temperature,,Pressure,Speed,Intensity,Dimensionless,Angle
    itemtype = "Number"

    labeltext = "das ist eine testzahl:"
    itemlabel = "[{labeltext}%.1f °]".format(labeltext=labeltext)
    itemcategory = "{}TestCategory".format(nameprefix)
    itemtags: List[str] = ["{}testtag1".format(nameprefix), "{}testtag2".format(nameprefix)]
    itemgroup_names: List[str] = ["{}testgroup1".format(nameprefix), "{}testgroup2".format(nameprefix)]
    grouptype = "{}testgrouptype".format(nameprefix)
    functionname = "{}testfunctionname".format(nameprefix)
    functionparams: List[str] = ["{}testfunctionnameParam1".format(nameprefix), "{}testfunctionnameParam2".format(nameprefix), "{}testfunctionnameParam3".format(nameprefix)]

    x2 = item_factory.create_or_update_item(name=itemname,
                                            data_type=itemtype,
                                            quantity_type=item_quantity_type,
                                            label=itemlabel,
                                            category=itemcategory,
                                            tags=itemtags,
                                            group_names=itemgroup_names,
                                            group_type=grouptype,
                                            function_name=functionname,
                                            function_params=functionparams)
    x2.state = 123.45
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert(itemtype+":"+item_quantity_type, x2.type_, "data_type")
    testutil.doassert(123.45, x2.state, "state")
    testutil.doassert(item_quantity_type, x2.quantityType, "quantity_type")
    testutil.doassert(itemlabel, x2.label, "label")
    testutil.doassert(itemcategory, x2.category, "category")
    for aExpectedTag in itemtags:
        testutil.doassert(True, aExpectedTag in x2.tags, "tag {}".format(aExpectedTag))

    for aExpectedGroupname in itemgroup_names:
        testutil.doassert(True, aExpectedGroupname in x2.groupNames, "tag {}".format(aExpectedGroupname))

    return x2


def testGroup(itemFactory, nameprefix) -> openhab.items.Item:
    itemtype = "Group"
    itemname = "{}TestGroup".format(nameprefix)
    testgroup_item = itemFactory.create_or_update_item(name=itemname, data_type=itemtype)
    return testgroup_item


def test_StringItem(item_factory, nameprefix):

    itemname = "{}CreateStringItemTest".format(nameprefix)
    itemtype = openhab.items.StringItem

    x2 = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    x2.state = "test string value 1"
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("test string value 1", x2.state, "itemstate")
    x2.state = "test string value 2"
    testutil.doassert("test string value 2", x2.state, "itemstate")



    return x2


def test_ContactItem(item_factory, nameprefix):

    itemname = "{}CreateContactItemTest".format(nameprefix)
    itemtype = openhab.items.ContactItem

    x2 = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    x2.state = "OPEN"
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("OPEN", x2.state, "itemstate")
    x2.state = "CLOSED"
    testutil.doassert("CLOSED", x2.state, "itemstate")
    try:
        x2.state = "SEPP"
        testutil.doassert(False, True, "this should have caused a exception!")
    except:
        pass

    return x2


def test_DateTimeItem(item_factory, nameprefix):

    itemname = "{}CreateDateTimeItemTest".format(nameprefix)
    itemtype = openhab.items.DateTimeItem

    x2 = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    log.info("current datetime in item:{}".format(x2.state))
    now = datetime.now()
    x2.state = now
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert(now, x2.state, "itemstate")
    return x2


def test_RollershutterItem(item_factory, nameprefix):

    itemname = "{}CreateRollershutterItemTest".format(nameprefix)
    itemtype = openhab.items.RollershutterItem

    x2: openhab.items.RollershutterItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.up()
    testutil.doassert(itemname, x2.name, "item_name")

    testutil.doassert("UP", x2.state, "itemstate")
    x2.state = 53
    testutil.doassert(53, x2.state, "itemstate")
    return x2


def test_ColorItem(item_factory, nameprefix):

    itemname = "{}CreateColorItemTest".format(nameprefix)
    itemtype = openhab.items.ColorItem

    x2: openhab.items.ColorItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.on()
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("ON", x2.state, "itemstate")
    new_value = 51,52,53
    x2.state = new_value

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert((51,52,53), x2.state, "itemstate")
    return x2


def test_DimmerItem(item_factory, nameprefix):

    itemname = "{}CreateDimmerItemTest".format(nameprefix)
    itemtype = openhab.items.DimmerItem

    x2: openhab.items.DimmerItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.on()
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("ON", x2.state, "itemstate")

    x2.off()
    testutil.doassert("OFF", x2.state, "itemstate")

    new_value = 51
    x2.state = new_value

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(new_value, x2.state, "itemstate")
    return x2


def test_SwitchItem(item_factory, nameprefix):

    itemname = "{}CreateSwitchItemTest".format(nameprefix)
    itemtype = openhab.items.SwitchItem

    x2: openhab.items.SwitchItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.on()
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("ON", x2.state, "itemstate")

    x2.off()
    testutil.doassert("OFF", x2.state, "itemstate")

    x2.toggle()
    testutil.doassert("ON", x2.state, "itemstate")

    new_value = "OFF"
    x2.state = new_value

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(new_value, x2.state, "itemstate")
    return x2


def test_PlayerItem(item_factory, nameprefix):
    itemname = "{}CreatePlayerItemTest".format(nameprefix)
    itemtype = openhab.items.PlayerItem

    x2: openhab.items.PlayerItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    x2.play()

    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("PLAY", x2.state, "itemstate")

    x2.pause()
    testutil.doassert("PAUSE", x2.state, "itemstate")
    return x2


myopenhab = openhab.OpenHAB(base_url, auto_update=False)
keeprunning = True
random.seed()
mynameprefix = "x2_{}".format(random.randint(1, 1000))

test_create_and_delete_items(myopenhab, mynameprefix)
# delete_all_items_starting_with(openhab,"x2_")

