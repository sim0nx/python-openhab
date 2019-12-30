.. image:: https://api.codacy.com/project/badge/Grade/c9f4e32e536f4150a8e7e18039f8f102
   :target: https://www.codacy.com/app/sim0nx/python-openhab?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sim0nx/python-openhab&amp;utm_campaign=Badge_Grade
   :alt: Codacy badge

.. image:: https://readthedocs.org/projects/python-openhab/badge/?version=latest
   :target: http://python-openhab.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://badge.fury.io/py/python-openhab.svg
   :target: https://badge.fury.io/py/python-openhab
   :alt: pypi version


python library for accessing the openHAB REST API
=================================================

This library allows for easily accessing the OpenHAB REST API.
A number of features are implemented but not all, this is work in progress.

Requirements
------------

  - python >= 3.5
  - python :: dateutil
  - python :: requests
  - python :: typing

Note on openHAB1:
-----------------

The current version is focused on OpenHAB 2.x; OpenHAB 1.x might still work, though this is not tested. If you require
older OpenHAB support, please use an older version of this library.

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


Note on NULL and UNDEF
----------------------

In OpenHAB items may have two states named NULL and UNDEF, which have distinct meanings but basically indicate that an
item has no usable value.
This library sets the state of an item, regardless of their OpenHAB value being NULL or UNDEF, to None.
This in order to ease working with the library as we do cast certain types to native types.

In order to check if an item's state is either NULL or UNDEF, you can use the helper functions:

.. code-block:: python

    item.is_state_null()
    item.is_state_undef()

