"""Полный прогон: генерация данных → замеры → сводка → графики.

Запуск:  python3 -m src.main [--skip-generate] [--order N]
"""

from __future__ import annotations

import argparse
import os

from src import analyze, benchmark, generate_data, plot


def main() -> None:
    p = argparse.ArgumentParser(description="Запуск всего пайплайна B*-дерева")
    p.add_argument(
        "--skip-generate",
        action="store_true",
        help="не перегенерировать data/input_10000.txt, если файл уже есть",
    )
    p.add_argument(
        "--order",
        type=int,
        default=benchmark.DEFAULT_ORDER,
        help="порядок B*-дерева (по умолчанию 5)",
    )
    args = p.parse_args()

    data_path = generate_data.DEFAULT_PATH
    if args.skip_generate and os.path.exists(data_path):
        print("шаг 1: пропускаем генерацию, файл уже существует")
    else:
        print("шаг 1: генерация входных данных")
        generate_data.main()

    print("шаг 2: замеры")
    benchmark.run(order=args.order)

    print("шаг 3: сводка")
    analyze.main()

    print("шаг 4: графики")
    plot.make_plots(order=args.order)

    print("готово.")


if __name__ == "__main__":
    main()
