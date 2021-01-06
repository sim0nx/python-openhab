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
import openhab
import openhab.events
import openhab.items as items
import openhab.ohtypes
import logging
import time

log = logging.getLogger(__name__)
logging.basicConfig(level=10, format="%(levelno)s:%(asctime)s - %(message)s - %(name)s - PID:%(process)d - THREADID:%(thread)d - %(levelname)s - MODULE:%(module)s, -FN:%(filename)s -FUNC:%(funcName)s:%(lineno)d")

log.error("xx")
log.warning("www")
log.info("iii")
log.debug("ddddd")

base_url = 'http://10.10.20.80:8080/rest'


def test_sinks(myopenhab: openhab.OpenHAB):
  log.info("starting tests 'test sinks'")
  ds=myopenhab.get_audio_defaultsink()
  log.info("defaultsink:{}".format(ds))
  allSinks=myopenhab.get_all_audiosinks()
  for aSink in allSinks:
    log.info("sink:{}".format(aSink))


def test_voices(myopenhab: openhab.OpenHAB):
  log.info("starting tests 'test voices'")
  dv=myopenhab.get_audio_defaultvoice()
  log.info("defaultvoice:{}".format(dv))
  allVoices=myopenhab.get_all_voices()
  for aVoice in allVoices:
    log.info("voice:{}".format(aVoice))

def test_voiceinterpreters(myopenhab: openhab.OpenHAB):
  log.info("starting tests 'test test_voiceinterpreters'")
  allVoice_interpreters = myopenhab.get_all_voicesinterpreters()
  for aVoiceinterpreter in allVoice_interpreters:
    log.info("voiceinterpreter:{}".format(aVoiceinterpreter))
  log.info("now get the 'system' voiceinterpreter")
  vi = myopenhab.get_voicesinterpreter("system")
  log.info("system voiceinterpreter:{}".format(vi))

def test_say(myopenhab: openhab.OpenHAB):
  myopenhab.get_audio_defaultvoice().say("das ist ein test",myopenhab.get_audio_defaultsink())

def test_interpret(myopenhab: openhab.OpenHAB):
  my_item_factory = openhab.items.ItemFactory(myopenhab)
  switchitem: openhab.items.SwitchItem = my_item_factory.create_or_update_item(name="test_interpret", label="test_interpret", data_type=openhab.items.SwitchItem)
  try:

    switchitem.off()
    time.sleep(0.3)
    vi = myopenhab.get_voicesinterpreter("system")
    text="schalte {} ein".format(switchitem.name)
    log.info("interpreting text:'{text}'".format(text=text))
    vi.interpret(text=text)
    time.sleep(0.3)
    switchitem.state == openhab.ohtypes.OnOffType.ON
  finally:
    switchitem.delete()






myopenhab = openhab.OpenHAB(base_url, auto_update=False)


# test_sinks(myopenhab)
# test_voices(myopenhab)
# test_voiceinterpreters(myopenhab)
# test_say(myopenhab)
test_interpret(myopenhab)