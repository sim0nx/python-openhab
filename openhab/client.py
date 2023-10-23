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

import datetime
import logging
import typing

import authlib.integrations.httpx_client
import httpx

import openhab.items
import openhab.rules

from .config import Oauth2Config, Oauth2Token

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class OpenHAB:
  """openHAB REST API client."""

  def __init__(self, base_url: str,
               username: typing.Optional[str] = None,
               password: typing.Optional[str] = None,
               http_auth: typing.Optional[httpx.Auth] = None,
               timeout: typing.Optional[float] = None,
               oauth2_config: typing.Optional[typing.Dict[str, typing.Any]] = None,
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
      http_auth (Auth, optional): An alternative to username/password pair, is to
                            specify a custom http authentication object of type :class:`requests.Auth`.
      timeout (float, optional): An optional timeout for REST transactions
      oauth2_config: Optional OAuth2 configuration dictionary

    Returns:
      OpenHAB: openHAB class instance.
    """
    self.url_rest = base_url
    self.url_base = base_url.rsplit('/', 1)[0]

    self.oauth2_config: typing.Optional[Oauth2Config] = None

    if oauth2_config is not None:
      self.oauth2_config = Oauth2Config(**oauth2_config)

      self.session = authlib.integrations.httpx_client.OAuth2Client(client_id=self.oauth2_config.client_id,
                                                                    token=self.oauth2_config.token.model_dump(),
                                                                    update_token=self._oauth2_token_updater,
                                                                    )

      self.session.metadata['token_endpoint'] = f'{self.url_rest}/auth/token'

      if not self.oauth2_config.token_cache.is_file():
        self._oauth2_token_updater(self.oauth2_config.token.model_dump())

    else:
      self.session = httpx.Client(timeout=timeout)

      if http_auth is not None:
        self.session.auth = http_auth
      elif not (username is None or password is None):
        self.session.auth = httpx.BasicAuth(username, password)

    self.logger = logging.getLogger(__name__)

    self._rules: typing.Optional[openhab.rules.Rules] = None

  @property
  def rules(self) -> openhab.rules.Rules:
    """Get object for managing rules."""
    if self._rules is None:
      self._rules = openhab.rules.Rules(self)

    return self._rules

  @staticmethod
  def _check_req_return(req: httpx.Response) -> None:
    """Internal method for checking the return value of a REST HTTP request.

    Args:
      req (requests.Response): A requests Response object.

    Returns:
      None: Returns None if no error occurred; else raises an exception.

    Raises:
      ValueError: Raises a ValueError exception in case of a non-successful
                  REST request.
    """
    if not 200 <= req.status_code < 300:
      req.raise_for_status()

  def req_get(self, uri_path: str, params: typing.Optional[typing.Union[typing.Dict[str, typing.Any], list, tuple]] = None) -> typing.Any:
    """Helper method for initiating a HTTP GET request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the GET request.

    Returns:
      dict: Returns a dict containing the data returned by the OpenHAB REST server.
    """
    r = self.session.get(f'{self.url_rest}{uri_path}', params=params)
    self._check_req_return(r)
    return r.json()

  def req_post(self,
               uri_path: str,
               data: typing.Optional[typing.Union[str, bytes, typing.Mapping[str, typing.Any], typing.Iterable[
                 typing.Tuple[str, typing.Optional[str]]]]] = None,
               ) -> None:
    """Helper method for initiating a HTTP POST request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the POST request.
      data (dict, optional): A optional dict with data to be submitted as part of the POST request.

    Returns:
      None: No data is returned.
    """
    headers = self.session.headers
    headers['Content-Type'] = 'text/plain'

    r = self.session.post(self.url_rest + uri_path, content=data, headers=headers)
    self._check_req_return(r)

  def req_put(self,
              uri_path: str,
              data: typing.Optional[dict] = None,
              json_data: typing.Optional[dict] = None,
              headers: typing.Optional[dict] = None,
              ) -> None:
    """Helper method for initiating a HTTP PUT request.

    Besides doing the actual request, it also checks the return value and returns the resulting decoded
    JSON data.

    Args:
      uri_path (str): The path to be used in the PUT request.
      data (dict, optional): A optional dict with data to be submitted as part of the PUT request.
      json_data: Data to be submitted as json.
      headers: Specify optional custom headers.

    Returns:
      None: No data is returned.
    """
    if headers is None:
      headers = {'Content-Type': 'text/plain'}
      content = data
      data = None
    else:
      content = None

    r = self.session.put(self.url_rest + uri_path, content=content, data=data, json=json_data, headers=headers)
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
      if i['name'] not in items:
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
      _type = json_data['groupType']

    if _type == 'Group' and 'groupType' not in json_data:
      return openhab.items.GroupItem(self, json_data)

    if _type == 'String':
      return openhab.items.StringItem(self, json_data)

    if _type == 'Switch':
      return openhab.items.SwitchItem(self, json_data)

    if _type == 'DateTime':
      return openhab.items.DateTimeItem(self, json_data)

    if _type == 'Contact':
      return openhab.items.ContactItem(self, json_data)

    if _type.startswith('Number'):
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
    return self.req_get(f'/items/{name}')

  def logout(self) -> bool:
    """OAuth2 session logout method.

    Returns:
      True or False depending on if the logout did succeed.
    """
    if self.oauth2_config is None or not isinstance(self.session, authlib.integrations.httpx_client.OAuth2Client):
      raise ValueError('You are trying to logout from a non-OAuth2 session. This is not supported!')

    data = {'refresh_token': self.oauth2_config.token.refresh_token,
            'id': self.oauth2_config.client_id,
            }
    url_logout = f'{self.url_rest}/auth/logout'

    res = self.session.post(url_logout, data=data)

    return res.status_code == 200

  def _oauth2_token_updater(self, token: typing.Dict[str, typing.Any],
                            refresh_token: typing.Any = None,
                            access_token: typing.Any = None) -> None:
    if self.oauth2_config is None:
      raise ValueError('OAuth2 configuration is not set; invalid action!')

    self.oauth2_config.token = Oauth2Token(**token)

    with self.oauth2_config.token_cache.open('w', encoding='utf-8') as fhdl:
      fhdl.write(self.oauth2_config.token.model_dump_json())

  def create_or_update_item(self,
                            name: str,
                            _type: typing.Union[str, typing.Type[openhab.items.Item]],
                            quantity_type: typing.Optional[str] = None,
                            label: typing.Optional[str] = None,
                            category: typing.Optional[str] = None,
                            tags: typing.Optional[typing.List[str]] = None,
                            group_names: typing.Optional[typing.List[str]] = None,
                            group_type: typing.Optional[typing.Union[str, typing.Type[openhab.items.Item]]] = None,
                            function_name: typing.Optional[str] = None,
                            function_params: typing.Optional[typing.List[str]] = None,
                            ) -> None:
    """Creates a new item in openHAB if there is no item with name 'name' yet.

    If there is an item with 'name' already in openHAB, the item gets updated with the infos provided. be aware that not provided fields will be deleted in openHAB.
    Consider to get the existing item via 'getItem' and then read out existing fields to populate the parameters here.

    Args:
      name: unique name of the item
      _type: the data_type used in openHAB (like Group, Number, Contact, DateTime, Rollershutter, Color, Dimmer, Switch, Player)
                       server.
                       To create groups use 'GroupItem'!
      quantity_type: optional quantity_type ( like Angle, Temperature, Illuminance (see https://www.openhab.org/docs/concepts/units-of-measurement.html))
      label: optional openHAB label (see https://www.openhab.org/docs/configuration/items.html#label)
      category: optional category. no documentation found
      tags: optional list of tags (see https://www.openhab.org/docs/configuration/items.html#tags)
      group_names: optional list of groups this item belongs to.
      group_type: Optional group_type (e.g. NumberItem, SwitchItem, etc).
      function_name: Optional function_name. no documentation found.
                     Can be one of ['EQUALITY', 'AND', 'OR', 'NAND', 'NOR', 'AVG', 'SUM', 'MAX', 'MIN', 'COUNT', 'LATEST', 'EARLIEST']
      function_params: Optional list of function params (no documentation found), depending on function name.
    """
    paramdict: typing.Dict[
      str, typing.Union[str, typing.List[str], typing.Dict[str, typing.Union[str, typing.List[str]]]]] = {}

    if isinstance(_type, type):
      if issubclass(_type, openhab.items.Item):
        itemtypename = _type.TYPENAME
      else:
        raise ValueError(
          f'_type parameter must be a valid subclass of type *Item* or a string name of such a class; given value is "{str(_type)}"')
    else:
      itemtypename = _type

    if quantity_type is None:
      paramdict['type'] = itemtypename
    else:
      paramdict['type'] = f'{itemtypename}:{quantity_type}'

    paramdict['name'] = name

    if label is not None:
      paramdict['label'] = label

    if category is not None:
      paramdict['category'] = category

    if tags is not None:
      paramdict['tags'] = tags

    if group_names is not None:
      paramdict['groupNames'] = group_names

    if group_type is not None:
      if isinstance(group_type, type):
        if issubclass(group_type, openhab.items.Item):
          paramdict['groupType'] = group_type.TYPENAME
        else:
          raise ValueError(
            f'group_type parameter must be a valid subclass of type *Item* or a string name of such a class; given value is "{str(group_type)}"')
      else:
        paramdict['groupType'] = group_type

    if function_name is not None:
      if function_name not in (
        'EQUALITY', 'AND', 'OR', 'NAND', 'NOR', 'AVG', 'SUM', 'MAX', 'MIN', 'COUNT', 'LATEST', 'EARLIEST'):
        raise ValueError(f'Invalid function name "{function_name}')

      if function_name in ('AND', 'OR', 'NAND', 'NOR') and (not function_params or len(function_params) != 2):
        raise ValueError(f'Group function "{function_name}" requires two arguments')

      if function_name == 'COUNT' and (not function_params or len(function_params) != 1):
        raise ValueError(f'Group function "{function_name}" requires one arguments')

      if function_params:
        paramdict['function'] = {'name': function_name, 'params': function_params}
      else:
        paramdict['function'] = {'name': function_name}

    self.logger.debug('About to create item with PUT request:\n%s', str(paramdict))

    self.req_put(f'/items/{name}', json_data=paramdict, headers={'Content-Type': 'application/json'})

  def get_item_persistence(self,
                           name: str,
                           service_id: typing.Optional[str] = None,
                           start_time: typing.Optional[datetime.datetime] = None,
                           end_time: typing.Optional[datetime.datetime] = None,
                           page: int = 0,
                           page_length: int = 0,
                           boundary: bool = False,
                           ) -> typing.Iterator[typing.Dict[str, typing.Union[str, int]]]:
    """Method for fetching persistence data for a given item.

    Args:
      name: The item name persistence data should be fetched for.
      service_id: ID of the persistence service. If not provided the default service will be used.
      start_time: Start time of the data to return. Will default to 1 day before end_time.
      end_time: End time of the data to return. Will default to current time.
      page: Page number of data to return. Defaults to 0 if not provided.
      page_length: The length of each page. Defaults to 0 which disabled paging.
      boundary: Gets one value before and after the requested period.

    Returns:
      Iterator over dict values containing time and state value, e.g.
        {"time": 1695588900122,
         "state": "23"
        }
    """
    params: typing.Dict[str, typing.Any] = {'boundary': str(boundary).lower(),
              'page': page,
              'pagelength': page_length,
              }

    if service_id is not None:
      params['serviceId'] = service_id

    if start_time is not None:
      params['starttime'] = start_time.isoformat()

    if end_time is not None:
      params['endtime'] = end_time.isoformat()

    if start_time == end_time:
      raise ValueError('start_time must differ from end_time')

    res = self.req_get(f'/persistence/items/{name}', params=params)

    yield from res['data']

    while page_length > 0 and int(res['datapoints']) > 0:
      params['page'] += 1
      res = self.req_get(f'/persistence/items/{name}', params=params)
      yield from res['data']
