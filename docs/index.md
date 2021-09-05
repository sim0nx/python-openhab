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

Assuming your openHAB instance runs at *http://127.0.0.1:8080* (replace with the correct one), use the following snippet
to retrieve a token:

```python
import pathlib
import openhab.oauth2_helper
import os
import json

url_base = 'http://127.0.0.1:8080'
api_username = 'admin'
api_password = 'admin'
oauth2_client_id = 'http://127.0.0.1/auth'
oauth2_token_cache = pathlib.Path(__file__).resolve().parent / '.oauth2_token_test'

# this must be set for oauthlib to work on http (do not set for https!)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

oauth2_token = openhab.oauth2_helper.get_oauth2_token(url_base, username=api_username, password=api_password)

with oauth2_token_cache.open('w') as fhdl:
    json.dump(oauth2_token, fhdl, indent=2, sort_keys=True)
```

The JSON that is returned is required for authenticating to openHAB using OAuth2 as well as a refresh token which is
used for refreshing a session.

Next try connecting to openHAB using this library as follows:

```python
import openhab
import pathlib
import json
import os

url_base = 'http://127.0.0.1:8080'
url_rest = f'{url_base}/rest'
oauth2_client_id = 'http://127.0.0.1/auth'
oauth2_token_cache = pathlib.Path(__file__).resolve().parent / '.oauth2_token_test'

# this must be set for oauthlib to work on http (do not set for https!)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

oauth2_config = {'client_id': oauth2_client_id,
                 'token_cache': str(oauth2_token_cache)
                 }

with oauth2_token_cache.open('r') as fhdl:
    oauth2_config['token'] = json.load(fhdl)

oh = openhab.OpenHAB(base_url=url_rest, oauth2_config=oauth2_config)

o = oh.get_item('test_item')
print(o)
```
