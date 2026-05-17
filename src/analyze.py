"""Подсчёт средних значений по результатам замеров.

Читает results/{insert,search,delete}_metrics.csv, выводит сводку в
results/summary.txt.

Запуск:  python3 -m src.analyze
"""

from __future__ import annotations

import csv
import os
import statistics
from typing import Iterable

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results",
)


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _stats(values: Iterable[float]) -> dict:
    vs = list(values)
    return {
        "count": len(vs),
        "mean": statistics.fmean(vs),
        "median": statistics.median(vs),
        "min": min(vs),
        "max": max(vs),
        "stdev": statistics.pstdev(vs) if len(vs) > 1 else 0.0,
    }


def summarize_csv(path: str) -> dict:
    rows = _read_csv(path)
    return {
        "time_ns": _stats(int(r["time_ns"]) for r in rows),
        "steps": _stats(int(r["steps"]) for r in rows),
    }


def main() -> None:
    summary = {
        "insert": summarize_csv(os.path.join(RESULTS_DIR, "insert_metrics.csv")),
        "search": summarize_csv(os.path.join(RESULTS_DIR, "search_metrics.csv")),
        "delete": summarize_csv(os.path.join(RESULTS_DIR, "delete_metrics.csv")),
    }

    txt_path = os.path.join(RESULTS_DIR, "summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Сводка замеров B*-дерева\n")
        f.write("=" * 50 + "\n\n")
        for op_name, op_label in (
            ("insert", "Вставка"),
            ("search", "Поиск"),
            ("delete", "Удаление"),
        ):
            s = summary[op_name]
            f.write(f"{op_label} (N={s['time_ns']['count']}):\n")
            f.write(
                "  время, нс: "
                f"среднее={s['time_ns']['mean']:.1f}, "
                f"медиана={s['time_ns']['median']:.1f}, "
                f"σ={s['time_ns']['stdev']:.1f}, "
                f"min={s['time_ns']['min']}, "
                f"max={s['time_ns']['max']}\n"
            )
            f.write(
                "  шаги    : "
                f"среднее={s['steps']['mean']:.2f}, "
                f"медиана={s['steps']['median']:.1f}, "
                f"σ={s['steps']['stdev']:.2f}, "
                f"min={s['steps']['min']}, "
                f"max={s['steps']['max']}\n\n"
            )

    print("сводка сохранена в", txt_path)
    # дублируем на стандартный вывод для удобства
    with open(txt_path, encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    main()
