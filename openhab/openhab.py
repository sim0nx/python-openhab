# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API"""

#
# Georges Toth (c) 2016-present <georges@trypill.org>
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

import requests
from requests.auth import HTTPBasicAuth
from openhab.items import Item, DateTimeItem, SwitchItem, NumberItem, ContactItem
import warnings
import typing

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class OpenHAB:
  """openHAB REST API client
  """

  def __init__(self, base_url: str,
               username: typing.Optional[str] = None,
               password: typing.Optional[str] = None,
               http_auth: typing.Optional[requests.auth.AuthBase] = None) -> None:
    """
    Args:
      base_url (str): The openHAB REST URL, e.g. http://example.com/rest
      username (str, optional): A optional username, used in conjunction with a optional
                      provided password, in case openHAB requires authentication.
      password (str, optional): A optional password, used in conjunction with a optional
                      provided username, in case openHAB requires authentication.
      http_auth (AuthBase, optional): An alternative to username/password pair, is to
                            specify a custom http authentication object of type :class:`requests.auth.AuthBase`.

    Returns:
      OpenHAB: openHAB class instance.
    """
    self.base_url = base_url

    self.session = requests.Session()
    self.session.headers['accept'] = 'application/json'

    if http_auth is not None:
      self.session.auth = http_auth
    elif not(username is None or password is None):
      self.session.auth = HTTPBasicAuth(username, password)

  @staticmethod
  def _check_req_return(req: requests.Response) -> None:
    """Internal method for checking the return value of a REST HTTP request.

    Args:
      req (requests.Response): A requests Response object.

    Returns:
      None: Returns None if no error occured; else raises an exception.

    Raises:
      ValueError: Raises a ValueError exception in case of a non-successful
                  REST request.
    """
    if not (200 <= req.status_code < 300):
      req.raise_for_status()

    return None

  def req_get(self, uri_path: str) -> typing.Any:
    """Helper method for initiating a HTTP GET request. Besides doing the actual
    request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the GET request.

    Returns:
      dict: Returns a dict containing the data returned by the openHAB REST server.
    """
    r = self.session.get(self.base_url + uri_path)
    self._check_req_return(r)
    return r.json()

  def req_post(self, uri_path: str, data: typing.Optional[dict]=None) -> None:
    """Helper method for initiating a HTTP POST request. Besides doing the actual
    request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the POST request.
      data (dict, optional): A optional dict with data to be submitted as part of the POST request.

    Returns:
      None: No data is returned.
    """
    r = self.session.post(self.base_url + uri_path, data=data)
    self._check_req_return(r)

    return None

  def req_put(self, uri_path: str, data: typing.Optional[dict]=None) -> None:
    """Helper method for initiating a HTTP PUT request. Besides doing the actual
    request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the PUT request.
      data (dict, optional): A optional dict with data to be submitted as part of the PUT request.

    Returns:
      None: No data is returned.
    """
    r = self.session.put(self.base_url + uri_path, data=data)
    self._check_req_return(r)

    return None

  # fetch all items
  def fetch_all_items(self) -> dict:
    """Returns all items defined in openHAB except for group-items

    Returns:
      dict: Returns a dict with item names as key and item class instances as value.
    """
    items = {}  # type: dict
    res = self.req_get('/items/')

    for i in res:
      # we ignore group-items for now
      if i['type'] == 'Group':
        continue

      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name: str) -> Item:
    """Returns an item with its state and type as fetched from openHAB

    Args:
      name (str): The name of the item to fetch from openHAB.

    Returns:
      Item: A corresponding Item class instance with the state of the requested item.
    """
    json_data = self.get_item_raw(name)

    return self.json_to_item(json_data)

  def json_to_item(self, json_data: dict) -> Item:
    """This method takes as argument the RAW (JSON decoded) response for an openHAB
    item. It checks of what type the item is and returns a class instance of the
    specific item filled with the item's state.

    Args:
      json_data (dict): The JSON decoded data as returned by the openHAB server.

    Returns:
      Item: A corresponding Item class instance with the state of the item.
    """
    if json_data['type'] == 'Switch':
      return SwitchItem(self, json_data)
    elif json_data['type'] == 'DateTime':
      return DateTimeItem(self, json_data)
    elif json_data['type'] == 'Contact':
      return ContactItem(self, json_data)
    elif json_data['type'] == 'Number':
      return NumberItem(self, json_data)
    else:
      return Item(self, json_data)

  def get_item_raw(self, name: str) -> typing.Any:
    """Private method for fetching a json configuration of an item.

    Args:
      name (str): The item name to be fetched.

    Returns:
      dict: A JSON decoded dict.
    """
    return self.req_get('/items/{}'.format(name))


class openHAB(OpenHAB):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    warnings.warn('The use of the "openHAB" class is deprecated, please use "OpenHAB" instead.', DeprecationWarning)
