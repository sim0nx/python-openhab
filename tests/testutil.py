# -*- coding: utf-8 -*-
"""utils for testing """

#
# Alexey Grubauer (c) 2020-present <alexey@ingenious-minds.at>
#
# python-openhab is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-openhab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-openhab.  If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=bad-indentation
import logging
from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable

log=logging.getLogger()

def doassert(expect:Any,actual:Any,label:Optional[str]=""):
    assert actual==expect, f"expected {label}:'{expect}', but it actually has '{actual}'".format(label=label,actual=actual,expect=expect)