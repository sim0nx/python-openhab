# -*- coding: utf-8 -*-
"""python classes for manipulating ui elements in openhab"""

#
# Alexey Grubauer (c) 2021 <alexey@ingenious-minds.at>
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
import dateutil.parser
import datetime
import json

class WidgetFactory:
  """A factory to get UI widgets from Openhab, create new or delete existing widgets in openHAB"""

  def __init__(self, openhab_client: openhab.client.OpenHAB):
    """Constructor.

        Args:
          openhab_client (openhab.OpenHAB): openHAB object.

        """
    self.openHABClient = openhab_client

  def get_widget(self, uid:str) -> Widget:
    url = "/ui/components/ui%3Awidget/{componentUID}".format(componentUID=uid)
    result_dict = self.openHABClient.req_get(url)
    widget = Widget(self.openHABClient, result_dict)
    return widget

  def exists_widget(self, uid:str) -> bool:
    try:
      existing_widget = self.get_widget(uid)
      return True
    except:
      return False

  def create_widget(self, uid:str, widget_code: typing.Optional[typing.Dict]=None):
    if self.exists_widget(uid):
      raise KeyError("UID '{}' already exists".format(uid))

    if widget_code is None:
      widget_code={"uid":uid, "timestamp":datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")}

    result = Widget(openhab_conn=self.openHABClient, widget=widget_code, loaded=False)
    result.uid = uid
    return result

  def delete_widget(self, uid:str) -> None:
    try:
      self.openHABClient.req_del("/ui/components/ui%3Awidget/{componentUID}".format(componentUID=uid))
    except:
      raise KeyError("UID '{}' does not exist".format(uid))



class Widget():
  def __init__(self, openhab_conn: openhab.client.OpenHAB, widget:typing.Dict, loaded:typing.Optional[bool]=True):
    self.openhab = openhab_conn
    self.code: typing.Dict = widget
    self._loaded = loaded
    self._changed_uid = False

  @property
  def uid(self) -> str:
    return self.code["uid"]


  @uid.setter
  def uid(self, uid: str) -> None:
    if uid != self.uid:
      self._changed_uid = True
    self.code["uid"] = uid



  @property
  def timestamp(self) -> datetime:
    return dateutil.parser.parse(self.code["timestamp"])

  @timestamp.setter
  def timestamp(self, timestamp: datetime) -> None:

    self.code["timestamp"] = timestamp.strftime("%b %d, %Y, %I:%M:%S %p")

  def __str__(self):
    return str(self.code)

  def set_code(self, code:typing.Dict):
    self.code = code

  def delete(self):
    self.openhab.req_del("/ui/components/ui%3Awidget/{componentUID}".format(componentUID=self.uid), headers = {'Content-Type': '*/*'})

  def save(self):
    code_str = json.dumps(self.code)
    if self._loaded and not self._changed_uid:
      #self.openhab.req_put("/ui/components/ui%3Awidget/{componentUID}".format(componentUID=self.uid), data=str(self.code), headers = {'Content-Type': 'application/json'})
      self.openhab.req_put("/ui/components/ui%3Awidget/{componentUID}".format(componentUID=self.uid), data=code_str, headers={'Content-Type': 'application/json'})
    else:
      #self.openhab.req_post("/ui/components/ui%3Awidget".format(componentUID=self.uid), data=str(self.code), headers = {'Content-Type': 'application/json'})
      self.openhab.req_post("/ui/components/ui%3Awidget".format(componentUID=self.uid), data=code_str, headers={'Content-Type': 'application/json'})
