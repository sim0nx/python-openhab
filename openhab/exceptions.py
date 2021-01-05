"""python-openhab exceptions."""


class OpenHABException(Exception):
  """Base of all python-openhab exceptions."""


class InvalidReturnException(OpenHABException):
  """The openHAB server returned an invalid or unparsable result."""
