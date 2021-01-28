# -*- coding: utf-8 -*-
"""python class to store historic data with a defined lifetime. Items older than seconds_of_history will be removed"""

#
# Alexey Grubauer (c) 2020 <alexey@ingenious-minds.at>
#

# pylint: disable=bad-indentation
from __future__ import annotations
from typing import TYPE_CHECKING, List, Set, Dict, Tuple, Union, Any, Optional, NewType, Callable, Generic, TypeVar
from datetime import datetime, timedelta


T = TypeVar("T")


class History(Generic[T]):
    def __init__(self, seconds_of_history: float) -> None:
        self.entries: List[Tuple[datetime, T]] = []
        self.history_lenght = timedelta(seconds=seconds_of_history)

    def add(self, item: T, when: datetime = None) -> None:
        if when is None:
            when = datetime.now()
        self.__clean_history__()
        self.entries.append((when, item))

    def __clean_history__(self) -> None:
        now = datetime.now()
        valid_until = now - self.history_lenght
        remove_from_idx = 0

        for entry in self.entries:
           if entry[0] < valid_until:
               remove_from_idx += 1
           else:
               break

        self.entries = self.entries[remove_from_idx:]

    def __contains__(self, item: T) -> bool:
      time,entry = self.get(item)
      if time is None:
        return False
      else:
        return True


    def clear(self):
        self.entries.clear()

    def get(self, item:T) -> (datetime,T):
      self.__clean_history__()
      for entry in reversed(self.entries):
        if entry[1] == item:
          return entry
      return None,None



    def get_entries(self) -> List[T]:
      self.__clean_history__()
      return [entry[1] for entry in self.entries]

    def remove(self, item: T = None, when: datetime = None) -> None:
      if item is None and when is None:
          return
      to_remove = []
      for entry in self.entries:
          if when is not None:
              if entry[0] == when:
                  to_remove.append(entry)
          if item is not None:
              if entry[1] == item:
                  to_remove.append(entry)
      for to_remove_entry in to_remove:
          try:
              self.entries.remove(to_remove_entry)
          except:
              pass
