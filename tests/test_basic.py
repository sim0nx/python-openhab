import datetime

import openhab

base_url = 'http://localhost:8080/rest'
openhab = openhab.OpenHAB(base_url)


def test_fetch_all_items():
  items = openhab.fetch_all_items()

  assert len(items)


def test_datetime_update():
  dt_obj = openhab.get_item('TheDateTime')
  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
  dt_obj.state = dt_utc_now

  assert dt_obj.state.isoformat(timespec='seconds') == dt_utc_now.isoformat(timespec='seconds')


def test_datetime_command():
  dt_obj = openhab.get_item('TheDateTime')
  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
  dt_obj.command(dt_utc_now)

  assert dt_obj.state.isoformat(timespec='seconds') == dt_utc_now.isoformat(timespec='seconds')


def test_null_undef():
  float_obj = openhab.get_item('floattest')

  float_obj.update_state_null()
  assert float_obj.is_state_null()

  float_obj.update_state_undef()
  assert float_obj.is_state_undef()


def test_float():
  float_obj = openhab.get_item('floattest')

  float_obj.state = 1.0
  assert float_obj.state == 1.0


def test_non_latin1_string():
  string_obj = openhab.get_item('stringtest')

  string_obj.state = 'שלום'
  assert string_obj.state == 'שלום'
