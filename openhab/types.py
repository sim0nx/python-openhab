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
from __future__ import annotations
import abc
import datetime
import re
import typing
import dateutil.parser

__author__ = 'Georges Toth <georges@trypill.org>'
__license__ = 'AGPLv3+'


class TypeNotImplementedError(NotImplementedError):
  """Exception raised for incoming OH events containing not implemented datatypes"""
  def __init__(self, itemname: str, datatype: str):
    self.itemname = itemname
    self.datatype = datatype


class CommandType(metaclass=abc.ABCMeta):
  """Base command data_type class."""

  TYPENAME = ""

  SUPPORTED_TYPENAMES = []
  UNDEF = 'UNDEF'
  NULL = 'NULL'
  UNDEFINED_STATES = [UNDEF, NULL]

  @classmethod
  def is_undefined(cls, value: typing.Any) -> bool:
    return value in CommandType.UNDEFINED_STATES

  @classmethod
  def get_type_for(cls, typename: str, parent_cls: typing.Optional[typing.Type[CommandType]] = None) -> typing.Union[typing.Type[CommandType], None]:
    if parent_cls is None:
      parent_cls = CommandType
    for a_type in parent_cls.__subclasses__():
      if typename in a_type.SUPPORTED_TYPENAMES:
        return a_type
      else:
        # mayba a subclass of a subclass
        result = a_type.get_type_for(typename, a_type)
        if result is not None:
          return result
    return None

  @classmethod
  @abc.abstractmethod
  def parse(cls, value: str) -> str:
    raise NotImplementedError()

  @classmethod
  @abc.abstractmethod
  def validate(cls, value: typing.Any) -> None:
    """Value validation method. As this is the base class which should not be used\
    directly, we throw a NotImplementedError exception.

    Args:
      value (Object): The value to validate. The data_type of the value depends on the item
                      data_type and is checked accordingly.

    Raises:
      NotImplementedError: Raises NotImplementedError as the base class should never
                           be used directly.
    """
    raise NotImplementedError()


class UndefType(CommandType):
  TYPENAME = "UnDef"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in UndefType.UNDEFINED_STATES:
      return None
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    pass


class GroupType(CommandType):
  TYPENAME = "Group"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in GroupType.UNDEFINED_STATES:
      return None
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    pass


class StringType(CommandType):
  """StringType data_type class."""

  TYPENAME = "String"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in StringType.UNDEFINED_STATES:
      return None
    if not isinstance(value, str):
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are any of data_type string.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    StringType.parse(value)


class OnOffType(StringType):
  """OnOffType data_type class."""
  TYPENAME = "OnOff"
  SUPPORTED_TYPENAMES = [TYPENAME]
  ON = "ON"
  OFF = "OFF"
  POSSIBLE_VALUES = [ON, OFF]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in OnOffType.UNDEFINED_STATES:
      return None
    if value not in OnOffType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``ON`` and ``OFF``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)
    OnOffType.parse(value)


class OpenCloseType(StringType):
  """OpenCloseType data_type class."""
  TYPENAME = "OpenClosed"
  SUPPORTED_TYPENAMES = [TYPENAME]
  OPEN = "OPEN"
  CLOSED = "CLOSED"
  POSSIBLE_VALUES = [OPEN, CLOSED]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in OpenCloseType.UNDEFINED_STATES:
      return None
    if value not in OpenCloseType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``OPEN`` and ``CLOSED``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)
    OpenCloseType.parse(value)


class ColorType(StringType):
  """ColorType data_type class."""
  TYPENAME = "HSB"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[typing.Tuple[int, int, float], None]:
    if value in ColorType.UNDEFINED_STATES:
      return None
    hs, ss, bs = re.split(',', value)
    h = int(hs)
    s = int(ss)
    b = float(bs)
    if not ((0 <= h <= 360) and (0 <= s <= 100) and (0 <= b <= 100)):
      raise ValueError()
    return h, s, b

  @classmethod
  def validate(cls, value: typing.Union[str, typing.Tuple[int, int, float]]) -> None:
    """Value validation method.

    Valid values are in format H,S,B.
    Value ranges:
      H(ue): 0-360
      S(aturation): 0-100
      B(rightness): 0-100

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    strvalue = str(value)
    if isinstance(value, tuple):
      if len(value) == 3:
        strvalue = "{},{},{}".format(value[0], value[1], value[2])
        super().validate(strvalue)
        ColorType.parse(strvalue)

    super().validate(strvalue)
    ColorType.parse(strvalue)


class DecimalType(CommandType):
  """DecimalType data_type class."""
  TYPENAME = "Decimal"
  SUPPORTED_TYPENAMES = [TYPENAME, "Quantity"]

  @classmethod
  def parse(cls, value: str) -> typing.Union[None, typing.Tuple[typing.Union[int, float], str]]:
    if value in DecimalType.UNDEFINED_STATES:
      return None

    m = re.match("(-?[0-9.]+)\s?(.*)?$", value)
    if m:
      value_value = m.group(1)
      value_unit_of_measure = m.group(2)
      try:
        return_value = int(value_value)
      except ValueError:
        try:
          return_value = float(value_value)
        except Exception as e:
          raise ValueError(e)
      return return_value, value_unit_of_measure
    raise ValueError()

  @classmethod
  def validate(cls, value: typing.Union[float, int]) -> None:
    """Value validation method.

    Valid values are any of data_type ``float`` or ``int``.

    Args:
      value (float): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    if not isinstance(value, (int, float)):
      raise ValueError()


class PercentType(DecimalType):
  """PercentType data_type class."""
  TYPENAME = "Percent"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[float, None]:
    if value in PercentType.UNDEFINED_STATES:
      return None
    try:
      f = float(value)
      if not 0 <= f <= 100:
        raise ValueError()
      return f
    except Exception as e:
      raise ValueError(e)

  @classmethod
  def validate(cls, value: typing.Union[float, int]) -> None:
    """Value validation method.

    Valid values are any of data_type ``float`` or ``int`` and must be greater of equal to 0
    and smaller or equal to 100.

    Args:
      value (float): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    if not 0 <= value <= 100:
      raise ValueError()


class IncreaseDecreaseType(StringType):
  """IncreaseDecreaseType data_type class."""
  TYPENAME = "IncreaseDecrease"
  SUPPORTED_TYPENAMES = [TYPENAME]

  INCREASE = "INCREASE"
  DECREASE = "DECREASE"

  POSSIBLE_VALUES = [INCREASE, DECREASE]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in IncreaseDecreaseType.UNDEFINED_STATES:
      return None
    if value not in IncreaseDecreaseType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``INCREASE`` and ``DECREASE``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)
    IncreaseDecreaseType.parse(value)


class DateTimeType(CommandType):
  """DateTimeType data_type class."""
  TYPENAME = "DateTime"
  SUPPORTED_TYPENAMES = [TYPENAME]

  @classmethod
  def parse(cls, value: str) -> typing.Union[datetime, None]:
    if value in DateTimeType.UNDEFINED_STATES:
      return None
    return dateutil.parser.parse(value)

  @classmethod
  def validate(cls, value: datetime.datetime) -> None:
    """Value validation method.

    Valid values are any of data_type ``datetime.datetime``.

    Args:
      value (datetime.datetime): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    if not isinstance(value, datetime.datetime):
      raise ValueError()


class UpDownType(StringType):
  """UpDownType data_type class."""

  TYPENAME = "UpDown"
  SUPPORTED_TYPENAMES = [TYPENAME]
  UP = "UP"
  DOWN = "DOWN"
  POSSIBLE_VALUES = [UP, DOWN]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in UpDownType.UNDEFINED_STATES:
      return None
    if value not in UpDownType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``UP`` and ``DOWN``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    UpDownType.parse(value)


class StopMoveType(StringType):
  """UpDownType data_type class."""

  TYPENAME = "StopMove"
  SUPPORTED_TYPENAMES = [TYPENAME]
  STOP = "STOP"
  POSSIBLE_VALUES = [STOP]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in StopMoveType.UNDEFINED_STATES:
      return None
    if value not in StopMoveType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``UP`` and ``DOWN``.

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    StopMoveType.parse(value)


class PlayPauseType(StringType):
  """PlayPauseType data_type class."""

  TYPENAME = "PlayPause"
  SUPPORTED_TYPENAMES = [TYPENAME]
  PLAY = "PLAY"
  PAUSE = "PAUSE"
  POSSIBLE_VALUES = [PLAY, PAUSE]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in PlayPauseType.UNDEFINED_STATES:
      return None
    if value not in PlayPauseType.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``PLAY``, ``PAUSE``

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    PlayPauseType.parse(value)


class NextPrevious(StringType):
  """NextPrevious data_type class."""

  TYPENAME = "NextPrevious"
  SUPPORTED_TYPENAMES = [TYPENAME]
  NEXT = "NEXT"
  PREVIOUS = "PREVIOUS"
  POSSIBLE_VALUES = [NEXT, PREVIOUS]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in NextPrevious.UNDEFINED_STATES:
      return None
    if value not in NextPrevious.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``PLAY``, ``PAUSE``

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    NextPrevious.parse(value)


class RewindFastforward(StringType):
  """RewindFastforward data_type class."""

  TYPENAME = "RewindFastforward"
  SUPPORTED_TYPENAMES = [TYPENAME]
  REWIND = "REWIND"
  FASTFORWARD = "FASTFORWARD"
  POSSIBLE_VALUES = [REWIND, FASTFORWARD]

  @classmethod
  def parse(cls, value: str) -> typing.Union[str, None]:
    if value in RewindFastforward.UNDEFINED_STATES:
      return None
    if value not in RewindFastforward.POSSIBLE_VALUES:
      raise ValueError()
    return value

  @classmethod
  def validate(cls, value: str) -> None:
    """Value validation method.

    Valid values are ``REWIND``, ``FASTFORWARD``

    Args:
      value (str): The value to validate.

    Raises:
      ValueError: Raises ValueError if an invalid value has been specified.
    """
    super().validate(value)

    RewindFastforward.parse(value)
