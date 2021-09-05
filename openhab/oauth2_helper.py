"""OAuth2 helper method for generating and fetching an OAuth2 token."""

import typing

import bs4
import requests


def get_oauth2_token(base_url: str,
                     username: str,
                     password: str,
                     client_id: typing.Optional[str] = None,
                     redirect_url: typing.Optional[str] = None,
                     scope: typing.Optional[str] = None
                     ) -> dict:
  """Method for generating an OAuth2 token.

  Args:
    base_url: openHAB base URL
    username: Admin account username
    password: Admin account password
    client_id: OAuth2 client ID; does not need to be specified
    redirect_url: OAuth2 redirect URL; does not need to be specified
    scope: Do not change unless you know what you are doing

  Returns:
    *dict* with the generated OAuth2 token details
  """
  if client_id is not None:
    oauth2_client_id = client_id
  else:
    oauth2_client_id = 'http://127.0.0.1/auth'

  if redirect_url is not None:
    oauth2_redirect_url = redirect_url
  else:
    oauth2_redirect_url = 'http://127.0.0.1/auth'

  if scope is not None:
    oauth2_scope = scope
  else:
    oauth2_scope = 'admin'

  oauth2_auth_endpoint = f'{base_url}/rest/auth/token'
  url_generate_token = f'{base_url}/auth?response_type=code&redirect_uri={oauth2_redirect_url}&client_id={oauth2_client_id}&scope={oauth2_scope}'

  res = requests.get(url_generate_token)
  res.raise_for_status()

  soup = bs4.BeautifulSoup(res.content, 'html.parser')
  submit_form = soup.find('form')

  action = submit_form.attrs.get('action').lower()
  url_submit_generate_token = f'{base_url}{action}'

  data = {}

  for input_tag in submit_form.find_all('input'):
    input_name = input_tag.attrs.get('name')

    if input_name is None:
      continue

    input_value = input_tag.attrs.get('value', '')

    data[input_name] = input_value

  data['username'] = username
  data['password'] = password

  res = requests.post(url_submit_generate_token, data=data, allow_redirects=False)
  res.raise_for_status()

  if 'location' not in res.headers:
    raise KeyError('Token generation failed!')

  oauth_redirect_location = res.headers['location']

  if '?code=' not in oauth_redirect_location:
    raise ValueError('Token generation failed!')

  oauth2_registration_code = oauth_redirect_location.split('?code=', 1)[1]

  data = {'grant_type': 'authorization_code',
          'code': oauth2_registration_code,
          'redirect_uri': oauth2_redirect_url,
          'client_id': oauth2_client_id,
          'refresh_token': None,
          'code_verifier': None
          }

  res = requests.post(oauth2_auth_endpoint, data=data)
  res.raise_for_status()

  oauth2_token = res.json()

  return oauth2_token
