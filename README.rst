.. image:: https://landscape.io/github/sim0nx/python-openhab/master/landscape.svg?style=flat
   :target: https://landscape.io/github/sim0nx/python-openhab/master
   :alt: Code Health

.. image:: https://readthedocs.org/projects/pip/badge/?version=latest
   :target: http://python-openhab.readthedocs.io/en/latest/
   :alt: Documentation

.. image:: https://www.quantifiedcode.com/api/v1/project/0cd779d9548547c09f69009316e548e1/badge.svg
  :target: https://www.quantifiedcode.com/app/project/0cd779d9548547c09f69009316e548e1
  :alt: Code issues


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

Installation
------------

Install the latest version using pip:

.. code-block:: bash

  pip install python-openhab


Example
-------

Example usage of the library:

.. code-block:: python

    from openhab import openHAB
    
    base_url = 'http://localhost:8080/rest'
    openhab = openHAB(base_url)
   
    # fetch all items
    items = openhab.fetch_all_items()
    
    sunset = items.get('Sunset')
    print(sunset.state)

    # fetch a single item
    item = openhab.get_item('light_switch')

    # turn a swith on
    item.on()

    # send a state update (this only update the state)
    item.state = 'OFF'

    # send a command
    item.command('ON')
