.. image:: https://landscape.io/github/sim0nx/python-openhab/master/landscape.svg?style=flat
   :target: https://landscape.io/github/sim0nx/python-openhab/master
   :alt: Code Health

.. image:: https://readthedocs.org/projects/pip/badge/?version=latest
   :target: http://python-openhab.readthedocs.io/en/latest/
   :alt: Documentation


python library for accessing the openHAB REST API
=================================================
  This library allows for easily accessing the openHAB REST API.
  A number of features are implemented but not all, this is work in progress.

Requirements
------------
  - python 2.7.x / 3.5
  - python :: dateutil
  - python :: requests

Note on openHAB1:
-----------------
  Make sure to use the 1.x branch for openHAB1.x!

Example
-------
  Example usage of the library::

    from openhab import openHAB
    
    base_url = 'http://localhost:8080/rest'
    openhab = openHAB(base_url)
   
    # fetch all items
    items = openhab.fetch_all_items()
    
    sunset = items.get('Sunset')
    print(sunset.state)

