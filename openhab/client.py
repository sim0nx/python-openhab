# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API."""

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
import json
import logging
import pathlib
import re
import time
import typing
import warnings

import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

import openhab.items

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class OpenHAB:
  """openHAB REST API client."""

  def __init__(self, base_url: str,
               username: typing.Optional[str] = None,
               password: typing.Optional[str] = None,
               http_auth: typing.Optional[requests.auth.AuthBase] = None,
               timeout: typing.Optional[float] = None,
               oauth2_config: typing.Optional[typing.Dict[str, typing.Any]] = None
               ) -> None:
    """Class constructor.

    The format of the optional *oauth2_config* dictionary is as follows:
    ```python
    {"client_id": "http://127.0.0.1/auth",
     "token_cache": "/<path>/<to>/.oauth2_token",
     "token":
       {"access_token": "adsafdasfasfsafasfsafasfasfasfsa....",
        "expires_in": 3600,
        "refresh_token": "312e21e21e32112",
        "scope": "admin",
        "token_type": "bearer",
        "user": {
          "name": "admin",
          "roles": [
            "administrator"
          ]
        }
    }
    ```

    Args:
      base_url (str): The openHAB REST URL, e.g. http://example.com/rest
      username (str, optional): A optional username, used in conjunction with a optional
                      provided password, in case openHAB requires authentication.
      password (str, optional): A optional password, used in conjunction with a optional
                      provided username, in case openHAB requires authentication.
      http_auth (AuthBase, optional): An alternative to username/password pair, is to
                            specify a custom http authentication object of type :class:`requests.auth.AuthBase`.
      timeout (float, optional): An optional timeout for REST transactions
      oauth2_config: Optional OAuth2 configuration dictionary

    Returns:
      OpenHAB: openHAB class instance.
    """
    self.url_rest = base_url
    self.url_base = base_url.rsplit('/', 1)[0]

    self.oauth2_config = oauth2_config

    if self.oauth2_config is not None:
      self._validate_oauth2_config(self.oauth2_config)

      if 'expires_at' not in self.oauth2_config['token']:
        self.oauth2_config['token']['expires_at'] = time.time() - 10

      self.session = OAuth2Session(self.oauth2_config['client_id'],
                                   token=self.oauth2_config['token'],
                                   auto_refresh_url=f'{self.url_rest}/auth/token',
                                   auto_refresh_kwargs={'client_id': self.oauth2_config['client_id']},
                                   token_updater=self._oauth2_token_updater
                                   )

      token_cache_path = pathlib.Path(self.oauth2_config['token_cache'])
      if not token_cache_path.is_file():
        self._oauth2_token_updater(self.oauth2_config['token'])

    else:
      self.session = requests.Session()

      if http_auth is not None:
        self.session.auth = http_auth
      elif not (username is None or password is None):
        self.session.auth = HTTPBasicAuth(username, password)

    self.session.headers['accept'] = 'application/json'

    self.timeout = timeout

    self.logger = logging.getLogger(__name__)

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
    if not 200 <= req.status_code < 300:
      req.raise_for_status()

  def req_get(self, uri_path: str) -> typing.Any:
    """Helper method for initiating a HTTP GET request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the GET request.

    Returns:
      dict: Returns a dict containing the data returned by the OpenHAB REST server.
    """
    r = self.session.get(self.url_rest + uri_path, timeout=self.timeout)
    self._check_req_return(r)
    return r.json()

  def req_post(self, uri_path: str, data: typing.Optional[dict] = None) -> None:
    """Helper method for initiating a HTTP POST request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the POST request.
      data (dict, optional): A optional dict with data to be submitted as part of the POST request.

    Returns:
      None: No data is returned.
    """
    r = self.session.post(self.url_rest + uri_path, data=data, headers={'Content-Type': 'text/plain'}, timeout=self.timeout)
    self._check_req_return(r)

  def req_put(self, uri_path: str, data: typing.Optional[dict] = None) -> None:
    """Helper method for initiating a HTTP PUT request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the PUT request.
      data (dict, optional): A optional dict with data to be submitted as part of the PUT request.

    Returns:
      None: No data is returned.
    """
    r = self.session.put(self.url_rest + uri_path, data=data, headers={'Content-Type': 'text/plain'}, timeout=self.timeout)
    self._check_req_return(r)

  # fetch all items
  def fetch_all_items(self) -> typing.Dict[str, openhab.items.Item]:
    """Returns all items defined in openHAB.

    Returns:
      dict: Returns a dict with item names as key and item class instances as value.
    """
    items = {}  # type: dict
    res = self.req_get('/items/')

    for i in res:
      if not i['name'] in items:
        items[i['name']] = self.json_to_item(i)

    return items

  def get_item(self, name: str) -> openhab.items.Item:
    """Returns an item with its state and type as fetched from openHAB.

    Args:
      name (str): The name of the item to fetch from openHAB.

    Returns:
      Item: A corresponding Item class instance with the state of the requested item.
    """
    json_data = self.get_item_raw(name)

    return self.json_to_item(json_data)

  def json_to_item(self, json_data: dict) -> openhab.items.Item:
    """This method takes as argument the RAW (JSON decoded) response for an openHAB item.

    It checks of what type the item is and returns a class instance of the
    specific item filled with the item's state.

    Args:
      json_data (dict): The JSON decoded data as returned by the openHAB server.

    Returns:
      Item: A corresponding Item class instance with the state of the item.
    """
    _type = json_data['type']
    if _type == 'Group' and 'groupType' in json_data:
      _type = json_data["groupType"]

    if _type == 'Switch':
      return openhab.items.SwitchItem(self, json_data)

    if _type == 'DateTime':
      return openhab.items.DateTimeItem(self, json_data)

    if _type == 'Contact':
      return openhab.items.ContactItem(self, json_data)

    if _type.startswith('Number'):
      if _type.startswith('Number:'):
        m = re.match(r'''^([^\s]+)''', json_data['state'])

        if m:
          json_data['state'] = m.group(1)

      return openhab.items.NumberItem(self, json_data)

    if _type == 'Dimmer':
      return openhab.items.DimmerItem(self, json_data)

    if _type == 'Color':
      return openhab.items.ColorItem(self, json_data)

    if _type == 'Rollershutter':
      return openhab.items.RollershutterItem(self, json_data)

    if _type == 'Player':
      return openhab.items.PlayerItem(self, json_data)

    return openhab.items.Item(self, json_data)

  def get_item_raw(self, name: str) -> typing.Any:
    """Private method for fetching a json configuration of an item.

    Args:
      name (str): The item name to be fetched.

    Returns:
      dict: A JSON decoded dict.
    """
    return self.req_get('/items/{}'.format(name))

  def logout(self) -> bool:
    """OAuth2 session logout method.

    Returns:
      True or False depending on if the logout did succeed.
    """
    if self.oauth2_config is None or not isinstance(self.session, OAuth2Session):
      raise ValueError('You are trying to logout from a non-OAuth2 session. This is not supported!')

    data = {'refresh_token': self.oauth2_config['token']['refresh_token'],
            'id': self.oauth2_config['client_id']
            }
    url_logout = f'{self.url_rest}/auth/logout'

    res = self.session.post(url_logout, data=data)

    return res.status_code == 200

  @staticmethod
  def _validate_oauth2_config(oauth2_config: typing.Dict[str, typing.Any]) -> bool:
    """Validate OAuth2 configuration."""
    if not ('client_id' in oauth2_config and 'token_cache' in oauth2_config and 'token' in oauth2_config):
      return False

    # pylint: disable=too-many-boolean-expressions
    if 'access_token' not in oauth2_config['token'] or \
      'expires_in' not in oauth2_config['token'] or \
      'refresh_token' not in oauth2_config['token'] or \
      'scope' not in oauth2_config['token'] or \
      'token_type' not in oauth2_config['token'] or \
      'user' not in oauth2_config['token'] or \
      'name' not in oauth2_config['token']['user'] or \
      'roles' not in oauth2_config['token']['user']:
      return False

    return True

  def _oauth2_token_updater(self, token: typing.Dict[str, typing.Any]) -> None:
    if self.oauth2_config is None:
      raise ValueError('OAuth2 configuration is not set; invalid action!')

    with open(self.oauth2_config['token_cache'], 'w', encoding='utf-8') as fhdl:
      json.dump(token, fhdl)


# noinspection PyPep8Naming
class openHAB(OpenHAB):
  """Legacy class wrapper, **do not** use."""

  def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
    """Constructor."""
    super().__init__(*args, **kwargs)

    warnings.warn('The use of the "openHAB" class is deprecated, please use "OpenHAB" instead.', DeprecationWarning)
