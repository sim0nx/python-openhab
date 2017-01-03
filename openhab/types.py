from __future__ import absolute_import, division, print_function, unicode_literals
# -*- coding: utf-8 -*-
'''python library for accessing the openHAB REST API'''

#
# Georges Toth (c) 2016 <georges@trypill.org>
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

import six
import datetime
import dateutil.parser

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class CommandType(object):
  '''Base command type class'''

  @classmethod
  def validate(cls, value):
    raise NotImplemented()


class StringType(CommandType):
  @classmethod
  def validate(cls, value):
    if not isinstance(value, six.string_types):
      raise ValueError()


class OnOffType(StringType):
  @classmethod
  def validate(cls, value):
    super(OnOffType, cls).validate(value)

    if value not in ['ON', 'OFF']:
      raise ValueError()


class OpenCloseType(StringType):
  @classmethod
  def validate(cls, value):
    super(OpenCloseType, cls).validate(value)

    if value not in ['OPEN', 'CLOSED']:
      raise ValueError()


class DecimalType(CommandType):
  @classmethod
  def validate(cls, value):
    if not (isinstance(value, float) or isinstance(value, int)):
      raise ValueError()


class PercentType(DecimalType):
  @classmethod
  def validate(cls, value):
    super(PercentType, cls).validate(value)

    if not (value >= 0 and value <= 100):
      raise ValueError()


class IncreaseDecreaseType(StringType):
  @classmethod
  def validate(cls, value):
    super(IncreaseDecreaseType, cls).validate(value)

    if value not in ['INCREASE', 'DECREASE']:
      raise ValueError()
