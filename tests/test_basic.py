import datetime
import time

import openhab

base_url = 'http://localhost:8080/rest'
oh = openhab.OpenHAB(base_url)


def test_fetch_all_items():
  items = oh.fetch_all_items()

  assert len(items)


def test_datetime_update():
  dt_obj = oh.get_item('TheDateTime')
  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
  dt_obj.state = dt_utc_now

  print(dt_obj.state)
  assert dt_obj.state.isoformat(timespec='seconds') == dt_utc_now.isoformat(timespec='seconds')


def test_datetime_command():
  dt_obj = oh.get_item('TheDateTime')
  dt_utc_now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
  dt_obj.command(dt_utc_now)

  assert dt_obj.state.isoformat(timespec='seconds') == dt_utc_now.isoformat(timespec='seconds')


def test_null_undef():
  float_obj = oh.get_item('floattest')

  float_obj.update_state_null()
  assert float_obj.is_state_null()

  float_obj.update_state_undef()
  assert float_obj.is_state_undef()


def test_float():
  float_obj = oh.get_item('floattest')

  float_obj.state = 1.0
  assert float_obj.state == 1.0


def test_scientific_notation():
  float_obj = oh.get_item('floattest')

  float_obj.state = 1e-10
  time.sleep(1)  # Allow time for OpenHAB test instance to process state update
  assert float_obj.state == 1e-10


def test_non_ascii_string():
  string_obj = oh.get_item('stringtest')

  string_obj.state = 'שלום'
  assert string_obj.state == 'שלום'

  string_obj.state = '°F'
  assert string_obj.state == '°F'


def test_color_item():
  coloritem = oh.get_item('color_item')

  coloritem.update_state_null()
  assert coloritem.is_state_null()

  coloritem.state = 1
  assert coloritem.state == (0.0, 0.0, 1.0)

  coloritem.state = '1.1, 1.2, 1.3'
  assert coloritem.state == (1.1, 1.2, 1.3)

  coloritem.state = 'OFF'
  assert coloritem.state == (1.1, 1.2, 0.0)

  coloritem.state = 'ON'
  assert coloritem.state == (1.1, 1.2, 100.0)


def test_number_temperature():
  # Tests below require the OpenHAB test instance to be configured with '°C' as
  # the unit of measure for the 'Dining_Temperature' item
  temperature_item = oh.get_item('Dining_Temperature')

  temperature_item.state = 1.0
  time.sleep(1)  # Allow time for OpenHAB test instance to process state update
  assert temperature_item.state == 1.0
  assert temperature_item.unit_of_measure == '°C'

  temperature_item.state = '2 °C'
  time.sleep(1)
  assert temperature_item.state == 2
  assert temperature_item.unit_of_measure == '°C'

  temperature_item.state = (3, '°C')
  time.sleep(1)
  assert temperature_item.state == 3
  assert temperature_item.unit_of_measure == '°C'

  # Unit of measure conversion (performed by OpenHAB server)
  temperature_item.state = (32, '°F')
  assert round(temperature_item.state, 2) == 0
  temperature_item.state = (212, '°F')
  time.sleep(1)
  assert temperature_item.state == 100
  assert temperature_item.unit_of_measure == '°C'
