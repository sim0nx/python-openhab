import unittest
from openhab.history import History
import time


class Item(object):
    def __init__(self, name: str):
        self.name = name
    def __str__(self):
      return "item:'{}'".format(self.name)


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.item_history: History[Item] = History[Item](0.3)


    def test_add_remove(self):
        a = Item("a")
        b = Item("b")

        self.item_history.add(a)
        self.item_history.add(b)

        self.assertIn(a, self.item_history)
        self.assertIn(b, self.item_history)
        self.item_history.remove(a)
        self.assertNotIn(a, self.item_history)
        self.assertIn(b, self.item_history)

        entries = self.item_history.get_entries()

        self.assertNotIn(a, entries)
        self.assertIn(b, entries)

        self.item_history.remove(a)
        self.assertNotIn(a, self.item_history)
        self.assertIn(b, self.item_history)
        self.item_history.remove(b)
        self.assertNotIn(a, self.item_history)
        self.assertNotIn(b, self.item_history)

    def test_stale(self):
        a = Item("a")
        b = Item("b")
        c = Item("c")

        self.item_history.clear()
        self.item_history.add(a)
        time.sleep(0.2)
        self.item_history.add(b)
        self.assertIn(a, self.item_history)
        self.assertIn(b, self.item_history)
        time.sleep(0.11)
        self.assertNotIn(a, self.item_history)
        self.assertIn(b, self.item_history)
        time.sleep(0.21)
        self.assertNotIn(a, self.item_history)
        self.assertNotIn(b, self.item_history)

        self.item_history.add(c)
        time.sleep(0.4)
        self.assertNotIn(a, self.item_history)
        self.assertNotIn(b, self.item_history)
        self.assertNotIn(c, self.item_history)

        entries = self.item_history.get_entries()
        self.assertEqual(len(entries), 0)

    def tearDown(self) -> None:
        self.item_history = None


if __name__ == '__main__':
    unittest.main()
