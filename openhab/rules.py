# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API."""

#
# Georges Toth (c) 2016-present <georges@trypill.org>
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
import typing

if typing.TYPE_CHECKING:
  import openhab.client

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class Rules:
  """Base rule class."""

  def __init__(self, openhab_conn: 'openhab.client.OpenHAB') -> None:
    """Constructor.

    Args:
      openhab_conn (openhab.OpenHAB): openHAB object.
    """
    self.openhab = openhab_conn
    self.logger = logging.getLogger(__name__)

  def get(self) -> typing.List[typing.Dict[str, typing.Any]]:
    """Get all rules."""
    return self.openhab.req_get('/rules')
