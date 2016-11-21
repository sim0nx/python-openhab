[![Code Health](https://landscape.io/github/sim0nx/python-openhab/master/landscape.svg?style=flat)](https://landscape.io/github/sim0nx/python-openhab/master)


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
  import openhab
  
  base_url = 'http://localhost:8080/rest'
  
  # fetch all items
  items = openhab.fetch_all_items(base_url)
  
  sunset = items.get('Sunset')
  print sunset.state
  ```
