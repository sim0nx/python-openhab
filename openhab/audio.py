# -*- coding: utf-8 -*-
"""python classes for accessing audio functions"""

#
# Alexey Grubauer (c) 2020 <alexey@ingenious-minds.at>
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
import typing
from dataclasses import dataclass
import openhab.types


class Audiosink:

  @staticmethod
  def json_to_audiosink(raw_json:typing.Dict, openhab:openhab.OpenHAB) -> Audiosink:
    new_audiosink = Audiosink(openhab=openhab, id=raw_json["id"], label=raw_json["label"])
    return new_audiosink


  def __init__(self, openhab:openhab.OpenHAB, id:str, label:str):
    self.openhab=openhab
    self.id = id
    self.label = label

  def say(self,text: str, voice:Voice):
    self.openhab.say(text=text,audiosinkid=self.id, voiceid=voice.id)

  def __str__(self):
    return "id:'{}', label:'{}'".format(self.id,self.label)


class Voice:
  @staticmethod
  def json_to_voice(raw_json: typing.Dict, openhab:openhab.OpenHAB) -> Voice:
    new_voice = Voice(openhab=openhab, id=raw_json["id"], label=raw_json["label"], locale=raw_json["locale"])
    return new_voice

  def __init__(self, openhab:openhab.OpenHAB, id: str, label: str, locale: str):
    self.openhab = openhab
    self.id = id
    self.label = label
    self.locale = locale

  def say(self,text: str, audiosink:Audiosink):
    audiosink.say(text=text,voice=self)

  def __str__(self):
    return "id:'{}', label:'{}', locale:'{}'".format(self.id, self.label,self.locale)


class Voiceinterpreter:
  @staticmethod
  def json_to_voiceinterpreter(raw_json: typing.Dict, openhab:openhab.OpenHAB) -> Voiceinterpreter:
    id: str = raw_json["id"]
    label: str = raw_json["label"]
    locales: typing.List[str] = []
    if "locales" in raw_json:
      locales = raw_json["locales"]
    new_voiceinterpreter = Voiceinterpreter(openhab=openhab, id=id, label=label, locales=locales)
    return new_voiceinterpreter

  def __init__(self, openhab:openhab.OpenHAB, id: str, label: str, locales: typing.List[str]):
    self.openhab = openhab
    self.id = id
    self.label = label
    self.locales = locales

  def interpret(self, text:str):
    self.openhab.interpret(text=text,voiceinterpreterid=self.id)

  def __str__(self):
    return "id:'{}', label:'{}', locales:'{}'".format(self.id, self.label,self.locales)