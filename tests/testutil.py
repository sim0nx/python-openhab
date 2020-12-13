import logging
from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable

log=logging.getLogger()

def doassert(expect:Any,actual:Any,label:Optional[str]=""):
    assert actual==expect, f"expected {label}:'{expect}', but it actually has '{actual}'".format(label=label,actual=actual,expect=expect)