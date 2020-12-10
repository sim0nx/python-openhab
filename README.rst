.. image:: https://api.codacy.com/project/badge/Grade/c9f4e32e536f4150a8e7e18039f8f102
   :target: https://www.codacy.com/app/sim0nx/python-openhab?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sim0nx/python-openhab&amp;utm_campaign=Badge_Grade
   :alt: Codacy badge

.. image:: https://readthedocs.org/projects/python-openhab/badge/?version=latest
   :target: http://python-openhab.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://badge.fury.io/py/python-openhab.svg
   :target: https://badge.fury.io/py/python-openhab
   :alt: pypi version

.. image:: https://travis-ci.com/sim0nx/python-openhab.svg?branch=master
   :target: https://travis-ci.com/sim0nx/python-openhab
   :alt: travis-ci status


python library for accessing the openHAB REST API
=================================================

This library allows for easily accessing the openHAB REST API.
A number of features are implemented but not all, this is work in progress.

currently you can
 - retrieve current state of items
 - send updates and commands to items
 - receive commands, updates and changes from openhab


Requirements
------------

  - python >= 3.5
  - python :: dateutil
  - python :: requests
  - python :: sseclient
  - openHAB version 2

Installation
------------

Install the latest version using pip:

.. code-block:: bash

  pip install python-openhab


Example
-------

Example usage of the library:

.. code-block:: python

    from openhab import OpenHAB
    
    base_url = 'http://localhost:8080/rest'
    openhab = OpenHAB(base_url,autoUpdate=True)
   
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

    # fetch some group
    lights_group = openhab.get_item('lights_group')

    # send command to group
    lights_group.on()

    # send update to each member
    for v in lights_group.members.values():
      v.update('OFF')

    # receive updates from openhab:

    # fetch a item and keep it
    testroom1_LampOnOff = openhab.get_item('light_switch')

    #define a callback function to receive events
    def onLight_switchCommand(item: openhab.items.Item, event: openhab.events.ItemCommandEvent):
        log.info("########################### COMMAND of {} to {} (itemsvalue:{}) from OPENHAB".format(event.itemname, event.newValueRaw, item.state))
        if event.source == openhab.events.EventSourceOpenhab:
            log.info("this change came from openhab")
    # install listener for evetns
    testroom1_LampOnOff.addEventListener(types=openhab.events.ItemCommandEventType, listener=onLight_switchCommand, onlyIfEventsourceIsOpenhab=False)
    # switch you will receive update also for your changes in the code. (see
    testroom1_LampOnOff.off()

    #Events stop to be delivered
    testroom1_LampOnOff=None

Note on NULL and UNDEF
----------------------

In openHAB items may have two states named NULL and UNDEF, which have distinct meanings but basically indicate that an
item has no usable value.
This library sets the state of an item, regardless of their openHAB value being NULL or UNDEF, to None.
This in order to ease working with the library as we do cast certain types to native types.

In order to check if an item's state is either NULL or UNDEF, you can use the helper functions:

.. code-block:: python

    item.is_state_null()
    item.is_state_undef()

