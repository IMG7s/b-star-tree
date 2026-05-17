"""Генерация входных данных: 10 000 уникальных целых из [1, 1 000 000].

Запуск:  python3 -m src.generate_data
Файл записывается в data/input_10000.txt (одно число на строку).
"""

from __future__ import annotations

import os
import random

DEFAULT_SEED = 42
DEFAULT_N = 10_000
DEFAULT_MAX = 1_000_000
DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "input_10000.txt",
)


def generate(
    n: int = DEFAULT_N,
    upper: int = DEFAULT_MAX,
    seed: int = DEFAULT_SEED,
) -> list[int]:
    """Сгенерировать список из ``n`` уникальных целых в [1, upper]."""
    if n > upper:
        raise ValueError(f"невозможно выбрать {n} уникальных из [1, {upper}]")
    rng = random.Random(seed)
    return rng.sample(range(1, upper + 1), n)


def save(values: list[int], path: str = DEFAULT_PATH) -> None:
    """Сохранить значения в файл (по одному на строку)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for v in values:
            f.write(f"{v}\n")


def load(path: str = DEFAULT_PATH) -> list[int]:
    """Прочитать список значений из файла."""
    with open(path, encoding="utf-8") as f:
        return [int(line) for line in f if line.strip()]


def main() -> None:
    values = generate()
    save(values)
    print(f"сохранено {len(values)} значений в {DEFAULT_PATH}")


if __name__ == "__main__":
    main()
