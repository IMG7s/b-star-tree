"""Юнит-тесты B*-дерева.

Запуск:  python3 -m unittest src.test_bstar_tree
        либо   python3 src/test_bstar_tree.py
"""

from __future__ import annotations

import random
import unittest

from src.bstar_tree import BStarTree


class BStarTreeTest(unittest.TestCase):
    def test_empty(self) -> None:
        t = BStarTree(order=5)
        t.validate()
        self.assertFalse(t.search(42))
        self.assertFalse(t.delete(42))

    def test_insert_ascending(self) -> None:
        t = BStarTree(order=5)
        for i in range(1, 51):
            t.insert(i)
            t.validate()
        for i in range(1, 51):
            self.assertTrue(t.search(i))
        self.assertFalse(t.search(0))
        self.assertFalse(t.search(51))

    def test_insert_descending(self) -> None:
        t = BStarTree(order=5)
        for i in range(50, 0, -1):
            t.insert(i)
            t.validate()
        for i in range(1, 51):
            self.assertTrue(t.search(i))

    def test_insert_duplicates_ignored(self) -> None:
        t = BStarTree(order=5)
        for _ in range(3):
            for i in range(1, 21):
                t.insert(i)
        t.validate()
        keys = list(t)
        self.assertEqual(keys, sorted(set(keys)))
        self.assertEqual(len(keys), 20)

    def test_random_insert_search(self) -> None:
        rng = random.Random(1)
        t = BStarTree(order=5)
        values = rng.sample(range(1, 100_000), 1000)
        for v in values:
            t.insert(v)
        t.validate()
        for v in values:
            self.assertTrue(t.search(v))
        for v in rng.sample(range(100_001, 200_000), 200):
            self.assertFalse(t.search(v))

    def test_random_delete_all(self) -> None:
        rng = random.Random(2)
        t = BStarTree(order=5)
        values = rng.sample(range(1, 100_000), 1000)
        for v in values:
            t.insert(v)
        order = list(values)
        rng.shuffle(order)
        for i, v in enumerate(order):
            self.assertTrue(t.delete(v))
            t.validate()
            # Удалённого ключа больше нет.
            self.assertFalse(t.search(v))
        self.assertEqual(list(t), [])

    def test_delete_missing(self) -> None:
        t = BStarTree(order=5)
        for v in [10, 20, 30, 40, 50]:
            t.insert(v)
        self.assertFalse(t.delete(99))
        t.validate()
        self.assertEqual(list(t), [10, 20, 30, 40, 50])

    def test_in_order_iteration(self) -> None:
        rng = random.Random(3)
        t = BStarTree(order=7)
        values = rng.sample(range(1, 10_000), 500)
        for v in values:
            t.insert(v)
        self.assertEqual(list(t), sorted(values))

    def test_step_counter_grows(self) -> None:
        t = BStarTree(order=5)
        t.reset_steps()
        before = t.steps
        for i in range(100):
            t.insert(i)
        self.assertGreater(t.steps, before)

    def test_various_orders(self) -> None:
        rng = random.Random(4)
        for m in (4, 5, 6, 7, 8, 16):
            t = BStarTree(order=m)
            values = rng.sample(range(1, 50_000), 300)
            for v in values:
                t.insert(v)
            t.validate()
            for v in values:
                self.assertTrue(t.search(v), f"miss with m={m}")
            rng.shuffle(values)
            for v in values[:200]:
                t.delete(v)
                t.validate()


if __name__ == "__main__":
    unittest.main()
