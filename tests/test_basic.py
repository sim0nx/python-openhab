import datetime

import openhab

base_url = 'http://localhost:8080/rest'
openhab = openhab.OpenHAB(base_url)


def test_fetch_all_items():
  items = openhab.fetch_all_items()

  assert len(items)


def test_datetime():
  dt_obj = openhab.get_item('TheDateTime')
  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

  dt_obj.state = dt_utc_now
  assert dt_obj.state.isoformat(timespec='milliseconds') == dt_utc_now.isoformat(timespec='milliseconds')

  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
  dt_obj.command(dt_utc_now)
  assert dt_obj.state.isoformat(timespec='milliseconds') == dt_utc_now.isoformat(timespec='milliseconds')


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
