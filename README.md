[![Code Health](https://landscape.io/github/sim0nx/python-openhab/2.0/landscape.svg?style=flat)](https://landscape.io/github/sim0nx/python-openhab/2.0)


python library for accessing the openHAB REST API
============
  This library allows for easily accessing the openHAB REST API.
  A number of features are implemented but not all, this is work in progress.

Requirements
------------
  - python 2.7.x
  - python-dateutil
  - python-requests

Note on openHAB2:
-----------
  Make sure to use the 2.0 branch for openHAB2!

Example
------------
  ```python
  from openhab import openHAB
  
  base_url = 'http://localhost:8080/rest'
  openhab = openHAB(base_url)
 
  # fetch all items
  items = openhab.fetch_all_items()
  
  sunset = items.get('Sunset')
  print sunset.state
  ```
