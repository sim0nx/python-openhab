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

import pathlib
import time
import typing

import pydantic

'''Considering a oauth2 token config is expected to look like the following:

```
{"client_id": "http://127.0.0.1/auth",
 "token_cache": "/<path>/<to>/.oauth2_token",
 "token": {
   "access_token": "adsafdasfasfsafasfsafasfasfasfsa....",
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
 }
```

, the following classes model that structure for validation.
'''


class Oauth2User(pydantic.BaseModel):
  """Nested user structure within an oauth2 token."""
  name: str
  roles: typing.List[str]


class Oauth2Token(pydantic.BaseModel):
  """Structure as returned by openHAB when generating a new oauth2 token."""
  access_token: str
  expires_in: int
  expires_at: float = time.time() - 10
  refresh_token: str
  scope: typing.Union[str, typing.List[str]] = 'admin'
  token_type: str
  user: Oauth2User


class Oauth2Config(pydantic.BaseModel):
  """Structure expected for a full oauth2 config."""
  client_id: str = 'http://127.0.0.1/auth'
  token_cache: pathlib.Path
  token: Oauth2Token
