# -*- coding: utf-8 -*-
"""tests for creating and deletion of items """

#
# Alexey Grubauer (c) 2020-present <alexey@ingenious-minds.at>
# Georges Toth (c) 2021-present <georges@trypill.org>
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

import logging
import random
from datetime import datetime
from typing import List

import pytest

import openhab
import openhab.events
import openhab.items as items
import openhab.ohtypes
import tests.testutil as testutil

log = logging.getLogger(__name__)
logging.basicConfig(level=10, format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("xx")
log.warning("www")
log.info("iii")
log.debug("ddddd")

base_url = 'http://localhost:8080/rest'

keeprunning = True
random.seed()
nameprefix = "x2_{}".format(random.randint(1, 1000))


@pytest.fixture
def myopenhab():
  return openhab.OpenHAB(base_url, auto_update=False, username='admin', password='admin')


def test_NumberItem(myopenhab: openhab.OpenHAB):
  item_factory = openhab.items.ItemFactory(myopenhab)
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

  try:
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
    testutil.doassert(itemtype + ":" + item_quantity_type, x2.type_, "data_type")
    testutil.doassert(123.45, x2.state, "state")
    testutil.doassert(item_quantity_type, x2.quantityType, "quantity_type")
    testutil.doassert(itemlabel, x2.label, "label")
    testutil.doassert(itemcategory, x2.category, "category")
    for aExpectedTag in itemtags:
      testutil.doassert(True, aExpectedTag in x2.tags, "tag {}".format(aExpectedTag))

    for aExpectedGroupname in itemgroup_names:
      testutil.doassert(True, aExpectedGroupname in x2.groupNames, "tag {}".format(aExpectedGroupname))
  finally:
    x2.delete()


def test_Group(myopenhab: openhab.OpenHAB) -> openhab.items.Item:
  itemtype = "Group"
  itemname = "{}TestGroup".format(nameprefix)
  item_factory = openhab.items.ItemFactory(myopenhab)
  testgroup_item = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
  return testgroup_item


def test_StringItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateStringItemTest".format(nameprefix)
  itemtype = openhab.items.StringItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2 = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    x2.state = "test string value 1"
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("test string value 1", x2.state, "itemstate")
    x2.state = "test string value 2"
    testutil.doassert("test string value 2", x2.state, "itemstate")
  finally:
    x2.delete()


def test_ContactItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateContactItemTest".format(nameprefix)
  itemtype = openhab.items.ContactItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
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
  finally:
    x2.delete()


def test_DateTimeItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateDateTimeItemTest".format(nameprefix)
  itemtype = openhab.items.DateTimeItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2 = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    log.info("current datetime in item:{}".format(x2.state))
    now = datetime.now()
    x2.state = now
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert(now, x2.state, "itemstate")
  finally:
    x2.delete()


def test_RollershutterItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateRollershutterItemTest".format(nameprefix)
  itemtype = openhab.items.RollershutterItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2: openhab.items.RollershutterItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.up()
    testutil.doassert(itemname, x2.name, "item_name")

    testutil.doassert("UP", x2.state, "itemstate")
    x2.state = 53
    testutil.doassert(53, x2.state, "itemstate")
  finally:
    x2.delete()


def test_ColorItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateColorItemTest".format(nameprefix)
  itemtype = openhab.items.ColorItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2: openhab.items.ColorItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.on()
    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("ON", x2.state, "itemstate")
    new_value = 51, 52, 53
    x2.state = new_value

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert((51, 52, 53), x2.state, "itemstate")
  finally:
    x2.delete()


def test_DimmerItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateDimmerItemTest".format(nameprefix)
  itemtype = openhab.items.DimmerItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
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
  finally:
    x2.delete()


def test_SwitchItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreateSwitchItemTest".format(nameprefix)
  itemtype = openhab.items.SwitchItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2: openhab.items.SwitchItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)

    x2.on()

    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("ON", x2.state, "itemstate")

    x2.off()
    testutil.doassert("OFF", x2.state, "itemstate")

    x2.toggle()
    testutil.doassert("ON", x2.state, "itemstate")

    new_value = openhab.ohtypes.OnOffType.OFF
    x2.state = new_value

    log.info("itemsate:{}".format(x2.state))
    testutil.doassert(new_value, x2.state, "itemstate")
  finally:
    x2.delete()


def test_PlayerItem(myopenhab: openhab.OpenHAB):
  itemname = "{}CreatePlayerItemTest".format(nameprefix)
  itemtype = openhab.items.PlayerItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  try:
    x2: openhab.items.PlayerItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
    x2.play()

    testutil.doassert(itemname, x2.name, "item_name")
    testutil.doassert("PLAY", x2.state, "itemstate")

    x2.pause()
    testutil.doassert("PAUSE", x2.state, "itemstate")
  finally:
    x2.delete()


def test_register_all_items(myopenhab: openhab.OpenHAB):
  itemname = "CreateSwitchItemTest_register_all_items"
  itemtype = openhab.items.SwitchItem
  item_factory = openhab.items.ItemFactory(myopenhab)

  x2: openhab.items.SwitchItem = item_factory.create_or_update_item(name=itemname, data_type=itemtype)
  try:
    myopenhab.register_all_items()
    for aItem in myopenhab.all_items.items():
      log.info("found item:{}".format(aItem))
    item_factory.get_item(itemname)


  finally:
    x2.delete()
