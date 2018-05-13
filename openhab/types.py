# -*- coding: utf-8 -*-
"""python library for accessing the openHAB REST API"""

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

import datetime
import abc
import typing

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class CommandType(metaclass=abc.ABCMeta):
  """Base command type class"""

  @classmethod
  @abc.abstractmethod
  def validate(cls, value: typing.Any):
    """Value validation method. As this is the base class which should not be used
    directly, we throw a NotImplementedError exception.

    Args:
      value (Object): The value to validate. The type of the value depends on the item
                      type and is checked accordingly.

    Raises:
      NotImplementedError: Raises NotImplementedError as the base class should never
                           be used directly.
    """
    raise NotImplementedError()


class StringType(CommandType):
  """StringType type class"""
  @classmethod
  def validate(cls, value: str):
    """Value validation method.
    Valid values are andy of type string.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    if not isinstance(value, str):
      raise ValueError()


class OnOffType(StringType):
  """OnOffType type class"""
  @classmethod
  def validate(cls, value: str):
    """Value validation method.
    Valid values are ``ON`` and ``OFF``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    if value not in ['ON', 'OFF']:
      raise ValueError()


class OpenCloseType(StringType):
  """OpenCloseType type class"""
  @classmethod
  def validate(cls, value: str):
    """Value validation method.
    Valid values are ``OPEN`` and ``CLOSED``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    if value not in ['OPEN', 'CLOSED']:
      raise ValueError()


class DecimalType(CommandType):
  """DecimalType type class"""
  @classmethod
  def validate(cls, value: typing.Union[float, int]):
    """Value validation method.
    Valid values are any of type ``float`` or ``int``.

    Args:
      value (float): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    if not (isinstance(value, float) or isinstance(value, int)):
      raise ValueError()


class PercentType(DecimalType):
  """PercentType type class"""
  @classmethod
  def validate(cls, value: typing.Union[float, int]):
    """Value validation method.
    Valid values are any of type ``float`` or ``int`` and must be greater of equal to 0
    and smaller or equal to 100.

    Args:
      value (float): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    if not (0 <= value <= 100):
      raise ValueError()


class IncreaseDecreaseType(StringType):
  """IncreaseDecreaseType type class"""
  @classmethod
  def validate(cls, value: str):
    """Value validation method.
    Valid values are ``INCREASE`` and ``DECREASE``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    if value not in ['INCREASE', 'DECREASE']:
      raise ValueError()


class DateTimeType(CommandType):
  """DateTimeType type class"""
  @classmethod
  def validate(cls, value: datetime.datetime):
    """Value validation method.
    Valid values are any of type ``datetime.datetime``.

    Args:
      value (datetime.datetime): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    if not isinstance(value, datetime.datetime):
      raise ValueError()
