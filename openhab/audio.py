# -*- coding: utf-8 -*-
"""Classes for accessing audio functions."""

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

import openhab.ohtypes


class Audiosink:

  @staticmethod
  def json_to_audiosink(raw_json: typing.Dict, openhab_client: openhab.OpenHAB) -> Audiosink:
    new_audiosink = Audiosink(openhab_client=openhab_client, _id=raw_json['id'], label=raw_json['label'])
    return new_audiosink

  def __init__(self, openhab_client: openhab.OpenHAB, _id: str, label: str) -> None:
    """Constructor."""
    self.openhab_client = openhab_client
    self.id = _id
    self.label = label

  def say(self, text: str, voice: Voice) -> None:
    self.openhab_client.say(text=text, audiosinkid=self.id, voiceid=voice.id)

  def __str__(self) -> str:
    """String representation of this class."""
    return f'id:"{self.id}", label:"{self.label}"'


class Voice:
  @staticmethod
  def json_to_voice(raw_json: typing.Dict, openhab_client: openhab.OpenHAB) -> Voice:
    new_voice = Voice(openhab_client=openhab_client, _id=raw_json['id'], label=raw_json['label'], locale=raw_json['locale'])
    return new_voice

  def __init__(self, openhab_client: openhab.OpenHAB, _id: str, label: str, locale: str) -> None:
    """Constructor."""
    self.openhab_client = openhab_client
    self.id = _id
    self.label = label
    self.locale = locale

  def say(self, text: str, audiosink: Audiosink) -> None:
    audiosink.say(text=text, voice=self)

  def __str__(self) -> str:
    """String representation of this class."""
    return f'id:"{self.id}", label:"{self.label}", locale:"{self.locale}"'


class Voiceinterpreter:
  @staticmethod
  def json_to_voiceinterpreter(raw_json: typing.Dict, openhab_client: openhab.OpenHAB) -> Voiceinterpreter:
    _id: str = raw_json['id']
    label: str = raw_json['label']
    locales: typing.List[str] = []
    if 'locales' in raw_json:
      locales = raw_json['locales']
    new_voiceinterpreter = Voiceinterpreter(openhab_client=openhab_client, _id=_id, label=label, locales=locales)
    return new_voiceinterpreter

  def __init__(self, openhab_client: openhab.OpenHAB, _id: str, label: str, locales: typing.List[str]) -> None:
    """Constructor."""
    self.openhab_client = openhab_client
    self.id = _id
    self.label = label
    self.locales = locales

  def interpret(self, text: str) -> None:
    self.openhab_client.interpret(text=text, voiceinterpreterid=self.id)

  def __str__(self) -> str:
    """String representation of this class."""
    return f'id:"{self.id}", label:"{self.label}", locales:"{self.locales}"'
