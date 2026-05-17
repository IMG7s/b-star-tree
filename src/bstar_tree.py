"""B*-дерево — реализация структуры данных для целочисленных ключей.

В B*-дереве, в отличие от обычного B-дерева, минимальное заполнение узла
составляет ≈ 2/3 от максимального (а не 1/2). Это достигается за счёт двух
дополнительных операций балансировки.

При переполнении узла сначала пробуется перераспределение ключей
с соседним узлом через ключ-разделитель в родителе. Только если соседи
тоже заполнены, выполняется 2-к-3 расщепление: два узла + разделитель
превращаются в три узла + два разделителя.

При недозаполнении узла сначала пробуется заём ключа у соседа.
Если оба соседа на минимуме, выполняется 3-к-2 слияние: три узла +
два разделителя превращаются в два узла + один разделитель.
В граничном случае (узел на краю — только один сосед) выполняется
обычное 2-к-1 слияние.

Подсчёт шагов:
    self.steps инкрементируется на каждое:
      • сравнение ключей (внутри двоичного поиска по узлу и в проверках
        равенства);
      • переход по указателю «потомок» или «родитель»;
      • перемещение/сдвиг ключа или указателя при балансировке.

Это даёт «иттерационный» аналог замера, который должен расти как
O(m · log_m n) по теории.
"""

from __future__ import annotations

import math
from typing import Iterator


class BStarNode:
    """Узел B*-дерева. Внутренний если children непуст, иначе лист."""

    __slots__ = ("keys", "children", "parent")

    def __init__(self) -> None:
        self.keys: list[int] = []
        self.children: list["BStarNode"] = []
        self.parent: "BStarNode | None" = None

    def is_leaf(self) -> bool:
        return not self.children


class BStarTree:
    """B*-дерево порядка ``order`` (m).

    Параметры:
        order: максимальное число потомков внутреннего узла (m). По умолчанию 5.
                Должен быть ≥ 4, иначе корректное 2/3-заполнение невозможно.

    Свойства:
        max_keys: m − 1 — максимум ключей в нелистовом неcorневом узле.
        min_keys: ⌈(2m − 1)/3⌉ − 1 — минимум ключей в неcorневом узле.
        root_max_keys: 2m − 1 — особое максимальное число ключей в корне;
            при превышении корень расщепляется 1-к-3 (вместо 1-к-2), благодаря
            чему даже первое расщепление сохраняет инвариант 2/3 у новых
            непосредственных потомков корня.
        steps: накопленный счётчик «шагов» алгоритма (см. модульный docstring).
    """

    def __init__(self, order: int = 5) -> None:
        if order < 4:
            raise ValueError("order должен быть не меньше 4")
        self.order = order
        self.max_keys = order - 1
        self.min_keys = math.ceil((2 * order - 1) / 3) - 1
        self.root_max_keys = 2 * self.max_keys + 1  # 2m − 1
        self.root: BStarNode = BStarNode()
        self.steps: int = 0

    def reset_steps(self) -> None:
        """Сбросить счётчик шагов в 0."""
        self.steps = 0

    # ---------------------------------------------------------------- поиск

    def search(self, key: int) -> bool:
        """Вернуть True, если ключ присутствует в дереве."""
        node = self.root
        while True:
            idx, found = self._bsearch(node.keys, key)
            if found:
                return True
            if node.is_leaf():
                return False
            self.steps += 1  # спуск к потомку
            node = node.children[idx]

    def _bsearch(self, keys: list[int], target: int) -> tuple[int, bool]:
        """Двоичный поиск с подсчётом сравнений.

        Возвращает (idx, found): idx — позиция совпадения или место вставки;
        found — True, если ``keys[idx] == target``.
        """
        lo, hi = 0, len(keys)
        while lo < hi:
            mid = (lo + hi) // 2
            self.steps += 1
            if keys[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(keys):
            self.steps += 1  # сравнение на равенство
            if keys[lo] == target:
                return lo, True
        return lo, False

    # -------------------------------------------------------------- вставка

    def insert(self, key: int) -> None:
        """Вставить ключ. Дубликаты игнорируются (молча)."""
        node = self.root
        while not node.is_leaf():
            idx, found = self._bsearch(node.keys, key)
            if found:
                return
            self.steps += 1
            node = node.children[idx]
        idx, found = self._bsearch(node.keys, key)
        if found:
            return
        node.keys.insert(idx, key)
        # сдвиг хвоста списка ключей при вставке
        self.steps += max(1, len(node.keys) - idx)
        self._fix_overflow(node)

    def _fix_overflow(self, node: BStarNode) -> None:
        """Восстановить инварианты переполнения снизу вверх.

        Для нелистового неcorневого узла: ``len(keys) ≤ max_keys``.
        Для корня: ``len(keys) ≤ root_max_keys``.
        """
        while True:
            if node.parent is None:
                if len(node.keys) > self.root_max_keys:
                    self._split_root_1_to_3(node)
                return
            if len(node.keys) <= self.max_keys:
                return
            parent = node.parent
            self.steps += 1  # подъём к родителю
            idx = parent.children.index(node)
            left_ok = idx > 0 and len(parent.children[idx - 1].keys) < self.max_keys
            right_ok = (
                idx < len(parent.children) - 1
                and len(parent.children[idx + 1].keys) < self.max_keys
            )
            if left_ok:
                self._rotate_overflow_to_left(parent, idx)
                return
            if right_ok:
                self._rotate_overflow_to_right(parent, idx)
                return
            # Оба соседа заполнены (или один отсутствует) → 2-к-3 расщепление.
            if idx < len(parent.children) - 1:
                self._split_2_to_3(parent, idx)
            else:
                self._split_2_to_3(parent, idx - 1)
            node = parent

    def _rotate_overflow_to_left(self, parent: BStarNode, idx: int) -> None:
        """Перенести один ключ из переполненного узла в левого соседа."""
        left = parent.children[idx - 1]
        node = parent.children[idx]
        sep = parent.keys[idx - 1]
        left.keys.append(sep)
        parent.keys[idx - 1] = node.keys.pop(0)
        self.steps += 2
        if not node.is_leaf():
            child = node.children.pop(0)
            child.parent = left
            left.children.append(child)
            self.steps += 1

    def _rotate_overflow_to_right(self, parent: BStarNode, idx: int) -> None:
        """Перенести один ключ из переполненного узла в правого соседа."""
        right = parent.children[idx + 1]
        node = parent.children[idx]
        sep = parent.keys[idx]
        right.keys.insert(0, sep)
        parent.keys[idx] = node.keys.pop()
        self.steps += 2
        if not node.is_leaf():
            child = node.children.pop()
            child.parent = right
            right.children.insert(0, child)
            self.steps += 1

    def _split_2_to_3(self, parent: BStarNode, left_idx: int) -> None:
        """2-к-3 расщепление пары узлов ``parent.children[left_idx, left_idx+1]``.

        Объединяются ключи обоих узлов + разделитель из родителя, затем
        делятся между тремя новыми узлами и двумя новыми разделителями.
        """
        left = parent.children[left_idx]
        right = parent.children[left_idx + 1]
        sep = parent.keys[left_idx]

        all_keys = left.keys + [sep] + right.keys
        is_leaf = left.is_leaf()
        all_children = [] if is_leaf else left.children + right.children
        self.steps += len(all_keys)

        total = len(all_keys)
        base = (total - 2) // 3
        rem = (total - 2) - 3 * base
        size_a = base + (1 if rem >= 1 else 0)
        size_b = base + (1 if rem >= 2 else 0)
        # размер третьего узла: total − 2 − size_a − size_b

        n1, n2, n3 = BStarNode(), BStarNode(), BStarNode()
        n1.keys = all_keys[:size_a]
        sep1 = all_keys[size_a]
        n2.keys = all_keys[size_a + 1 : size_a + 1 + size_b]
        sep2 = all_keys[size_a + 1 + size_b]
        n3.keys = all_keys[size_a + 2 + size_b :]

        if not is_leaf:
            split1 = size_a + 1
            split2 = size_a + size_b + 2
            n1.children = all_children[:split1]
            n2.children = all_children[split1:split2]
            n3.children = all_children[split2:]
            for c in n1.children:
                c.parent = n1
            for c in n2.children:
                c.parent = n2
            for c in n3.children:
                c.parent = n3

        n1.parent = parent
        n2.parent = parent
        n3.parent = parent
        parent.children[left_idx : left_idx + 2] = [n1, n2, n3]
        parent.keys[left_idx : left_idx + 1] = [sep1, sep2]
        self.steps += 2

    def _split_root_1_to_3(self, node: BStarNode) -> None:
        """1-к-3 расщепление корня.

        Корень может вырастать до 2m − 1 ключей; превысив этот порог,
        он расщепляется на три новых узла + 2 разделителя в новом корне.
        Каждый из трёх новых потомков получает не меньше ``min_keys``
        ключей, что и обеспечивает 2/3-инвариант на самом верхнем уровне.
        """
        all_keys = node.keys
        is_leaf = node.is_leaf()
        all_children = [] if is_leaf else node.children
        total = len(all_keys)
        self.steps += total

        base = (total - 2) // 3
        rem = (total - 2) - 3 * base
        size_a = base + (1 if rem >= 1 else 0)
        size_b = base + (1 if rem >= 2 else 0)

        n1, n2, n3 = BStarNode(), BStarNode(), BStarNode()
        n1.keys = all_keys[:size_a]
        sep1 = all_keys[size_a]
        n2.keys = all_keys[size_a + 1 : size_a + 1 + size_b]
        sep2 = all_keys[size_a + 1 + size_b]
        n3.keys = all_keys[size_a + 2 + size_b :]
        if not is_leaf:
            split1 = size_a + 1
            split2 = size_a + size_b + 2
            n1.children = all_children[:split1]
            n2.children = all_children[split1:split2]
            n3.children = all_children[split2:]
            for c in n1.children:
                c.parent = n1
            for c in n2.children:
                c.parent = n2
            for c in n3.children:
                c.parent = n3

        new_root = BStarNode()
        new_root.keys = [sep1, sep2]
        new_root.children = [n1, n2, n3]
        n1.parent = new_root
        n2.parent = new_root
        n3.parent = new_root
        self.root = new_root
        self.steps += 2

    # -------------------------------------------------------------- удаление

    def delete(self, key: int) -> bool:
        """Удалить ключ. Возвращает True, если ключ был найден и удалён."""
        node, idx = self._find(self.root, key)
        if node is None:
            return False
        if node.is_leaf():
            node.keys.pop(idx)
            self.steps += 1
            self._fix_underflow(node)
        else:
            # Замена на in-order предшественника из листа.
            pred_node = node.children[idx]
            self.steps += 1
            while not pred_node.is_leaf():
                self.steps += 1
                pred_node = pred_node.children[-1]
            pred = pred_node.keys[-1]
            node.keys[idx] = pred
            pred_node.keys.pop()
            self.steps += 2
            self._fix_underflow(pred_node)
        # Опустошённый внутренний корень заменяется на единственного потомка.
        if not self.root.keys and self.root.children:
            self.root = self.root.children[0]
            self.root.parent = None
        return True

    def _find(self, root: BStarNode, key: int) -> tuple[BStarNode | None, int]:
        node = root
        while True:
            idx, found = self._bsearch(node.keys, key)
            if found:
                return node, idx
            if node.is_leaf():
                return None, -1
            self.steps += 1
            node = node.children[idx]

    def _fix_underflow(self, node: BStarNode) -> None:
        """Восстановить инвариант ``len(keys) ≥ min_keys`` снизу вверх."""
        while node.parent is not None and len(node.keys) < self.min_keys:
            parent = node.parent
            self.steps += 1
            idx = parent.children.index(node)
            left = parent.children[idx - 1] if idx > 0 else None
            right = (
                parent.children[idx + 1] if idx < len(parent.children) - 1 else None
            )
            # 1. Заём у непосредственного соседа, если у того есть запас.
            if left is not None and len(left.keys) > self.min_keys:
                self._borrow_from_left(parent, idx)
                return
            if right is not None and len(right.keys) > self.min_keys:
                self._borrow_from_right(parent, idx)
                return
            # 2. Балансировка с двумя соседями. При >=3 потомков родителя
            # выбираем тройку подряд идущих узлов (включая текущий) и решаем:
            # если суммарного количества ключей хватает на три узла по
            # min_keys (плюс 2 разделителя) — выполняем 3-к-3 перераспределение
            # (родитель ничего не теряет); иначе — 3-к-2 слияние (родитель
            # теряет один ключ-разделитель, что может вызвать дальнейшее
            # недозаполнение). Граничный случай «у родителя ровно 2 потомка»
            # бывает только если родитель — корень; тогда 2-к-1 слияние и
            # объединённый узел становится новым корнем.
            n = len(parent.children)
            if n >= 3:
                if idx == 0:
                    left_idx = 0
                elif idx == n - 1:
                    left_idx = n - 3
                else:
                    left_idx = idx - 1
                merged = self._rebalance_three(parent, left_idx)
                if not merged:
                    return
            else:
                self._merge_2_to_1(parent, 0)
            node = parent

    def _borrow_from_left(self, parent: BStarNode, idx: int) -> None:
        left = parent.children[idx - 1]
        node = parent.children[idx]
        sep = parent.keys[idx - 1]
        node.keys.insert(0, sep)
        parent.keys[idx - 1] = left.keys.pop()
        self.steps += 2
        if not node.is_leaf():
            child = left.children.pop()
            child.parent = node
            node.children.insert(0, child)
            self.steps += 1

    def _borrow_from_right(self, parent: BStarNode, idx: int) -> None:
        right = parent.children[idx + 1]
        node = parent.children[idx]
        sep = parent.keys[idx]
        node.keys.append(sep)
        parent.keys[idx] = right.keys.pop(0)
        self.steps += 2
        if not node.is_leaf():
            child = right.children.pop(0)
            child.parent = node
            node.children.append(child)
            self.steps += 1

    def _rebalance_three(self, parent: BStarNode, left_idx: int) -> bool:
        """Универсальная балансировка трёх соседних потомков.

        Если суммарного количества ключей трёх узлов вместе с двумя
        разделителями достаточно для трёх узлов по ``min_keys`` ключей плюс
        два разделителя — выполняется 3-к-3 перераспределение, и родитель
        не теряет ключей. Иначе выполняется 3-к-2 слияние: три узла
        превращаются в два, родитель теряет один разделитель.

        Возвращает True если произошло слияние (требуется проверять
        родителя на недозаполнение), False если только перераспределение.
        """
        a = parent.children[left_idx]
        b = parent.children[left_idx + 1]
        c = parent.children[left_idx + 2]
        s1 = parent.keys[left_idx]
        s2 = parent.keys[left_idx + 1]
        all_keys = a.keys + [s1] + b.keys + [s2] + c.keys
        is_leaf = a.is_leaf()
        all_children = [] if is_leaf else a.children + b.children + c.children
        self.steps += len(all_keys)

        total = len(all_keys)
        if total >= 3 * self.min_keys + 2:
            # 3-к-3 перераспределение.
            keys_for_children = total - 2
            base = keys_for_children // 3
            rem = keys_for_children - 3 * base
            size_a = base + (1 if rem >= 1 else 0)
            size_b = base + (1 if rem >= 2 else 0)
            n1, n2, n3 = BStarNode(), BStarNode(), BStarNode()
            n1.keys = all_keys[:size_a]
            sep1 = all_keys[size_a]
            n2.keys = all_keys[size_a + 1 : size_a + 1 + size_b]
            sep2 = all_keys[size_a + 1 + size_b]
            n3.keys = all_keys[size_a + 2 + size_b :]
            if not is_leaf:
                split1 = size_a + 1
                split2 = size_a + size_b + 2
                n1.children = all_children[:split1]
                n2.children = all_children[split1:split2]
                n3.children = all_children[split2:]
                for cc in n1.children:
                    cc.parent = n1
                for cc in n2.children:
                    cc.parent = n2
                for cc in n3.children:
                    cc.parent = n3
            n1.parent = parent
            n2.parent = parent
            n3.parent = parent
            parent.children[left_idx : left_idx + 3] = [n1, n2, n3]
            parent.keys[left_idx : left_idx + 2] = [sep1, sep2]
            self.steps += 2
            return False
        else:
            # 3-к-2 слияние.
            keys_for_children = total - 1
            left_size = keys_for_children // 2
            n1, n2 = BStarNode(), BStarNode()
            n1.keys = all_keys[:left_size]
            sep = all_keys[left_size]
            n2.keys = all_keys[left_size + 1 :]
            if not is_leaf:
                n1.children = all_children[: left_size + 1]
                n2.children = all_children[left_size + 1 :]
                for cc in n1.children:
                    cc.parent = n1
                for cc in n2.children:
                    cc.parent = n2
            n1.parent = parent
            n2.parent = parent
            parent.children[left_idx : left_idx + 3] = [n1, n2]
            parent.keys[left_idx : left_idx + 2] = [sep]
            self.steps += 1
            return True

    def _merge_2_to_1(self, parent: BStarNode, left_idx: int) -> None:
        """Граничный случай: 2 узла + разделитель → 1 узел."""
        a = parent.children[left_idx]
        b = parent.children[left_idx + 1]
        s = parent.keys[left_idx]
        merged = BStarNode()
        merged.keys = a.keys + [s] + b.keys
        if not a.is_leaf():
            merged.children = a.children + b.children
            for cc in merged.children:
                cc.parent = merged
        merged.parent = parent
        self.steps += len(merged.keys)
        parent.children[left_idx : left_idx + 2] = [merged]
        parent.keys[left_idx : left_idx + 1] = []
        self.steps += 1

    # --------------------------------------------------------- сервисные

    def __iter__(self) -> Iterator[int]:
        """In-order обход (без подсчёта шагов)."""

        def walk(node: BStarNode) -> Iterator[int]:
            if node.is_leaf():
                yield from node.keys
                return
            for i, k in enumerate(node.keys):
                yield from walk(node.children[i])
                yield k
            yield from walk(node.children[-1])

        yield from walk(self.root)

    def height(self) -> int:
        h = 0
        node = self.root
        while not node.is_leaf():
            node = node.children[0]
            h += 1
        return h

    # ------------------------------------------------------ валидация

    def validate(self) -> None:
        """Проверить инварианты B*-дерева. Бросает AssertionError при нарушении."""
        if not self.root.keys and not self.root.children:
            return
        depths: list[int] = []
        self._validate_recursive(self.root, is_root=True, depth=0, depths=depths)
        if len(set(depths)) > 1:
            raise AssertionError(f"листья на разных уровнях: {sorted(set(depths))}")

    def _validate_recursive(
        self,
        node: BStarNode,
        *,
        is_root: bool,
        depth: int,
        depths: list[int],
    ) -> None:
        for i in range(1, len(node.keys)):
            if node.keys[i - 1] >= node.keys[i]:
                raise AssertionError(
                    f"неотсортированные ключи в узле: {node.keys}"
                )
        if is_root:
            limit = self.root_max_keys
            if len(node.keys) > limit:
                raise AssertionError(
                    f"переполнение корня: {len(node.keys)} > {limit}"
                )
        else:
            if len(node.keys) > self.max_keys:
                raise AssertionError(
                    f"переполнение узла: {len(node.keys)} > {self.max_keys}"
                )
            if len(node.keys) < self.min_keys:
                raise AssertionError(
                    f"недозаполнение узла: {len(node.keys)} < {self.min_keys}"
                )
        if node.is_leaf():
            depths.append(depth)
            return
        if len(node.children) != len(node.keys) + 1:
            raise AssertionError(
                f"несовпадение: {len(node.children)} детей, {len(node.keys)} ключей"
            )
        for i, c in enumerate(node.children):
            if c.parent is not node:
                raise AssertionError("неверный указатель на родителя")
            for k in c.keys:
                if i > 0 and k <= node.keys[i - 1]:
                    raise AssertionError(
                        f"нарушение порядка: ключ {k} в потомке {i} ≤ разделителю "
                        f"{node.keys[i - 1]}"
                    )
                if i < len(node.keys) and k >= node.keys[i]:
                    raise AssertionError(
                        f"нарушение порядка: ключ {k} в потомке {i} ≥ разделителю "
                        f"{node.keys[i]}"
                    )
            self._validate_recursive(c, is_root=False, depth=depth + 1, depths=depths)
