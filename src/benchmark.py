"""Замеры работы B*-дерева: вставка, поиск, удаление.

Замеряется только время и число шагов самих операций — без I/O и без
работы с файлами. Результаты пишутся в CSV.

Запуск:  python3 -m src.benchmark
"""

from __future__ import annotations

import csv
import os
import random
import time

from src.bstar_tree import BStarTree
from src.generate_data import DEFAULT_PATH as DATA_PATH, load

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results",
)

DEFAULT_ORDER = 5
DEFAULT_SEED = 12345
SEARCH_COUNT = 100
DELETE_COUNT = 1000


def _ensure_results_dir() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)


def _write_csv(path: str, header: list[str], rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def benchmark_insert(tree: BStarTree, values: list[int]) -> list[list]:
    """Поэлементно вставить все значения; вернуть строки CSV."""
    rows: list[list] = []
    for i, v in enumerate(values):
        tree.reset_steps()
        t0 = time.perf_counter_ns()
        tree.insert(v)
        t1 = time.perf_counter_ns()
        rows.append([i, v, t1 - t0, tree.steps])
    return rows


def benchmark_search(tree: BStarTree, keys: list[int]) -> list[list]:
    rows: list[list] = []
    for i, v in enumerate(keys):
        tree.reset_steps()
        t0 = time.perf_counter_ns()
        found = tree.search(v)
        t1 = time.perf_counter_ns()
        rows.append([i, v, t1 - t0, tree.steps, int(found)])
    return rows


def benchmark_delete(tree: BStarTree, keys: list[int]) -> list[list]:
    rows: list[list] = []
    for i, v in enumerate(keys):
        tree.reset_steps()
        t0 = time.perf_counter_ns()
        ok = tree.delete(v)
        t1 = time.perf_counter_ns()
        rows.append([i, v, t1 - t0, tree.steps, int(ok)])
    return rows


def run(
    order: int = DEFAULT_ORDER,
    seed: int = DEFAULT_SEED,
    data_path: str = DATA_PATH,
) -> None:
    _ensure_results_dir()
    values = load(data_path)
    rng = random.Random(seed)

    print(f"загружено {len(values)} значений; m={order}")

    tree = BStarTree(order=order)
    insert_rows = benchmark_insert(tree, values)
    print(
        f"вставка: {len(insert_rows)} операций; "
        f"высота дерева = {tree.height()}"
    )
    _write_csv(
        os.path.join(RESULTS_DIR, "insert_metrics.csv"),
        ["index", "key", "time_ns", "steps"],
        insert_rows,
    )

    search_keys = rng.sample(values, SEARCH_COUNT)
    search_rows = benchmark_search(tree, search_keys)
    print(f"поиск: {len(search_rows)} операций")
    _write_csv(
        os.path.join(RESULTS_DIR, "search_metrics.csv"),
        ["index", "key", "time_ns", "steps", "found"],
        search_rows,
    )

    # Удаляем непересекающуюся со списком поиска подвыборку — иначе
    # поиск/удаление будут зависеть друг от друга по содержимому, что
    # затруднит интерпретацию замеров. Берём независимую случайную выборку.
    delete_keys = rng.sample(values, DELETE_COUNT)
    delete_rows = benchmark_delete(tree, delete_keys)
    print(f"удаление: {len(delete_rows)} операций")
    _write_csv(
        os.path.join(RESULTS_DIR, "delete_metrics.csv"),
        ["index", "key", "time_ns", "steps", "deleted"],
        delete_rows,
    )

    print("замеры сохранены в", RESULTS_DIR)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
