import os
import pathlib

import pytest

import openhab.oauth2_helper

# ruff: noqa: S106

@pytest.fixture(scope='session')
def oh() -> 'openhab.OpenHAB':
  """Setup a generic connection."""
  base_url = 'http://localhost:8080/rest'
  return openhab.OpenHAB(base_url)


@pytest.fixture(scope='session')
def oh_oauth2() -> 'openhab.OpenHAB':
  """Setup a generic connection."""
  url_base = 'http://localhost:8080'
  url_rest = f'{url_base}/rest'

  # this must be set for oauthlib to work on http
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

  oauth2_token = openhab.oauth2_helper.get_oauth2_token(url_base, username='admin', password='admin')

  oauth2_config = {'client_id': r'http://127.0.0.1/auth',
                   'token_cache': str(pathlib.Path(__file__).resolve().parent.parent / '.oauth2_token_test'),
                   'token': oauth2_token,
                   }

  return openhab.OpenHAB(url_rest, oauth2_config=oauth2_config)
