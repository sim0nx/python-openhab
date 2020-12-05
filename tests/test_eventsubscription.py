from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable

import openhab
import openhab.events
import time
import openhab.items as items
import logging
log=logging.getLogger()
logging.basicConfig(level=0)

log.error("xx")
log.warning("www")
log.info("iii")
log.debug("ddddd")



base_url = 'http://10.10.20.81:8080/rest'



testdata:Dict[str,Tuple[str,str]]={'OnOff'           : ('ItemStateEvent','{"type":"OnOff","value":"ON"}'),
                                   'Decimal'         : ('ItemStateEvent','{"type":"Decimal","value":"170.0"}'),
                                   'DateTime'        : ('ItemStateEvent','{"type":"DateTime","value":"2020-12-04T15:53:33.968+0100"}'),
                                   'UnDef'           : ('ItemStateEvent','{"type":"UnDef","value":"UNDEF"}'),
                                   'String'          : ('ItemStateEvent','{"type":"String","value":"WANING_GIBBOUS"}'),
                                   'Quantitykm'      : ('ItemStateEvent','{"type":"Quantity","value":"389073.99674024084 km"}'),
                                   'Quantitykm grad' : ('ItemStateEvent', '{"type":"Quantity","value":"233.32567712620255 °"}'),
                                   'Quantitywm2'     : ('ItemStateEvent', '{"type":"Quantity","value":"0.0 W/m²"}'),
                                   'Percent'         : ('ItemStateEvent', '{"type":"Percent","value":"52"}'),
                                   'UpDown'          : ('ItemStateEvent', '{"type":"UpDown","value":"DOWN"}'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   # 'XXX   ': ('ItemStateEvent', 'XXXXXXXXXXXXXXXXXXXX'),
                                   #

                                   'OnOffChange'                   : ('ItemStateChangedEvent','{"type":"OnOff","value":"OFF","oldType":"OnOff","oldValue":"ON"}'),
                                   'DecimalChange'                 : ('ItemStateChangedEvent','{"type":"Decimal","value":"170.0","oldType":"Decimal","oldValue":"186.0"}'),
                                   'QuantityChange'                : ('ItemStateChangedEvent','{"type":"Quantity","value":"389073.99674024084 km","oldType":"Quantity","oldValue":"389076.56223012594 km"}'),
                                   'QuantityGradChange'            : ('ItemStateChangedEvent', '{"type":"Quantity","value":"233.32567712620255 °","oldType":"Quantity","oldValue":"233.1365666436372 °"}'),
                                   'DecimalChangeFromNull'         : ('ItemStateChangedEvent', '{"type":"Decimal","value":"0.5","oldType":"UnDef","oldValue":"NULL"}'),
                                   'DecimalChangeFromNullToUNDEF'  : ('ItemStateChangedEvent', '{"type":"Decimal","value":"15","oldType":"UnDef","oldValue":"NULL"}'),
                                   'PercentChange'                 : ('ItemStateChangedEvent', '{"type":"Percent","value":"52","oldType":"UnDef","oldValue":"NULL"}'),

                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   # 'XXX': ('ItemStateChangedEvent', 'XXXXXXXXXX'),
                                   'Datatypechange'                : ('ItemStateChangedEvent', '{"type":"OnOff","value":"ON","oldType":"UnDef","oldValue":"NULL"}')
                                   }

def executeParseCheck():
    for testkey in testdata:
        log.info("testing:{}".format(testkey))
        stringToParse=testdata[testkey]


if True:
    myopenhab = openhab.OpenHAB(base_url,autoUpdate=True)

    # allitems:List[items.Item] = openhab.fetch_all_items()
    # for aItem in allitems:
    #
    #     print(aItem)

    itemDimmer=myopenhab.get_item("testroom1_LampDimmer")
    print(itemDimmer)
    itemAzimuth=myopenhab.get_item("testworld_Azimuth")
    print(itemAzimuth)
    itemClock=myopenhab.get_item("myClock")
    itemDimmer.command(12.5)


    def onAzimuthChange(item:openhab.items.Item ,event:openhab.events.ItemStateEvent):
        log.info("########################### UPDATE of {} to {} (itemsvalue:{}) from OPENHAB ONLY".format(event.itemname,event.newValue, item.state))

    itemAzimuth.addEventListener(openhab.events.ItemCommandEventType,onAzimuthChange,onlyIfEventsourceIsOpenhab=True)


    # def onAzimuthChangeAll(item:openhab.items.Item ,event:openhab.events.ItemStateEvent):
    #     if event.source == openhab.events.EventSourceInternal:
    #         log.info("########################### UPDATE of {} to {} (itemsvalue:{}) from internal".format(event.itemname,event.newValue, item.state))
    #     else:
    #         log.info("########################### UPDATE of {} to {} (itemsvalue:{}) from OPENHAB".format(event.itemname, event.newValue, item.state))
    #
    # itemAzimuth.addEventListener(openhab.events.ItemCommandEventType,onAzimuthChangeAll,onlyIfEventsourceIsOpenhab=False)

    #print(itemClock)
    while True:
        time.sleep(10)
        x=0
        x=2
        if x==1:
            itemAzimuth=None
        elif x==2:
            itemAzimuth.command(55.1)