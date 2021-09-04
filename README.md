[![Travis CI](https://travis-ci.com/sim0nx/python-openhab.svg?branch=master)](https://travis-ci.com/sim0nx/python-openhab)
[![Documentation Status](https://readthedocs.org/projects/python-openhab/badge/?version=latest)](http://python-openhab.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://badge.fury.io/py/python-openhab.svg)](https://badge.fury.io/py/python-openhab)

# python library for accessing the openHAB REST API

This library allows for easily accessing the openHAB REST API. A number of features are implemented but not all, this is
work in progress.

# Requirements

- python >= 3.5
- python :: dateutil
- python :: requests
- openHAB version 3

Installation
------------

Install the latest version using pip:

```shell
pip install python-openhab
```

# Example

Example usage of the library:

```python

from openhab import OpenHAB

base_url = 'http://localhost:8080/rest'
openhab = OpenHAB(base_url)

# fetch all items
items = openhab.fetch_all_items()

sunset = items.get('Sunset')
print(sunset.state)

# fetch a single item
item = openhab.get_item('light_switch')

# turn a switch on
item.on()

# send a state update (this only update the state)
item.state = 'OFF'

# send a command
item.command('ON')

# check if item state is NULL
if item.state is None and item.is_state_null():
    pass

# check if item state is UNDEF
if item.state is None and item.is_state_undef():
    pass

# fetch some group
lights_group = openhab.get_item('lights_group')

# send command to group
lights_group.on()

# send update to each member
for v in lights_group.members.values():
    v.update('OFF')
```

# Note on NULL and UNDEF

In openHAB items may have two states named NULL and UNDEF, which have distinct meanings but basically indicate that an
item has no usable value. This library sets the state of an item, regardless of their openHAB value being NULL or UNDEF,
to None. This in order to ease working with the library as we do cast certain types to native types.

In order to check if an item's state is either NULL or UNDEF, you can use the helper functions:

```python
item.is_state_null()
item.is_state_undef()
```

# Experimental OAuth2 Support

In order to try out OAuth2 authentication, you first need to register with the openHAB endpoint in order to retrieve a
token and refresh token.

Assuming your openHAB instance runs at *http://127.0.0.1:8080* (replace with the correct one), do the following:

Open in browser:
http://127.0.0.1:8080/auth?response_type=code&redirect_uri=http://127.0.0.1/auth&client_id=http://127.0.0.1/auth&scope=admin

Which should redirect to a URL which looks like the following one:
http://127.0.0.1/auth?code=41e3262910914230b9bb745e676b32c9

Create and fetch the session using curl (**code** is contained in the URL you got redirected to in the previous step):

```shell
CLIENT_ID="http://127.0.0.1/auth"
CODE="<code>"
AUTH_ENDPOINT="http://127.0.0.1:8080/rest/auth/token"

curl -X POST -i \
    $AUTH_ENDPOINT \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code" \
    -d "code=${CODE}" \
    -d "redirect_uri=${CLIENT_ID}" \
    -d "client_id=${CLIENT_ID}" \
    -d "refresh_token=" \
    -d "code_verifier="
```

The JSON that is returned is required for authenticating to openHAB usin OAuth2 as well as a refresh token which is used
for refreshing a session.

Make sure *requests_oauthlib* is installed:

```shell
pip install requests_oauthlib
```

Next try connecting to openHAB using this library as follows:

```python
import openhab
from requests_oauthlib import OAuth2Session

token = {
    'access_token': 'eyJraWQiOm51bGwsImFsZyI6IlJTMjU2In0.eyJpc3MiOiJvcGVuaGFiIiwiYXVkIjoib3BlbmhhYiIsImV4cCI6MTYzMDc3MDc1NiwianRpIjoiekMxXy1qWk5tVTE0bGd1bkV6SjZDUSIsImlhdCI6MTYzMDc2NzE1NiwibmJmIjoxNjMwNzY3MDM2LCJzdWIiOiJhZG1pbiIsImNsaWVudF9pZCI6Imh0dHA6Ly8xMjcuMC4wLjEvYXV0aCIsInNjb3BlIjoiYWRtaW4iLCJyb2xlIjpbImFkbWluaXN0cmF0b3IiXX0.PEUGJHdbCrcd61gZqS5S-pCm_hgBcGanXjnk_5VOpN2VPDhNbZ1iNhQe6UICcaHLjOYFKjr3mduRD5WmTIRfZYwFu7vOkULMzuDV26LdoFmpc46C-_IUHA0o5kqD25CpHFfH-uBiwWwGraMK5ii9i5V7QwKTi65unjrjywAUDDsm6NpbmF1IAURrN9ScTLHEMVJaq3RUJsSIa-lYDWHEgOhnYkISOeecia0pXMibuH_phsco16WmUdQwu-x8tNiyPeiGvIOZoLGTO4O2YTnDunekP_JG-DkEWUIC3lf1iwz9l8GsASeegpEQH8pPVkGELTUn669nGdhoFEFiYabaow',
    'refresh_token': 'fc53ecc0530e4f69ab9c82faf5a8ca81',
    'token_type': 'Bearer',
    'expires_in': '3600'
}

client_id = r'http://127.0.0.1/auth'
refresh_url = 'http://127.0.0.1:8080/rest/auth/token'
protected_url = 'http://127.0.0.1:8080/rest/auth/sessions'


def token_saver(raw):
    """Dummy "token updated" hook."""
    print('updated token:')
    print(raw)
    print()


base_url = 'http://127.0.0.1:8080/rest'

client = OAuth2Session(client_id, token=token, auto_refresh_url=refresh_url,
                       auto_refresh_kwargs={'client_id': client_id}, token_updater=token_saver)
oh = openhab.OpenHAB(base_url=base_url, session=client)

o = oh.get_item('test_item')

print(o)
```
