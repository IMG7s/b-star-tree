"""Построение графиков по результатам замеров.

Читает results/*_metrics.csv, сохраняет PNG в results/.
Графики строятся попарно для каждой операции: время и число шагов
в зависимости от номера операции. Поверх практических данных
наносится скользящее среднее и теоретическая кривая c · log_m(размер).

Запуск:  python3 -m src.plot [--order m]
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from typing import Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results",
)

DEFAULT_ORDER = 5
WINDOW = 200  # окно скользящего среднего для вставки
SEARCH_WINDOW = 10
DELETE_WINDOW = 50


def _read_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _moving_average(values: Sequence[float], window: int) -> list[float]:
    if window <= 1:
        return list(values)
    out: list[float] = []
    s = 0.0
    from collections import deque
    q: deque[float] = deque()
    for v in values:
        q.append(v)
        s += v
        if len(q) > window:
            s -= q.popleft()
        out.append(s / len(q))
    return out


def _plot_op(
    ax_time,
    ax_steps,
    rows: list[dict],
    op_title: str,
    *,
    order: int,
    window: int,
    tree_size_for_op,
):
    """Построить пару графиков для одной операции на двух осях."""
    idx = [int(r["index"]) for r in rows]
    times = [int(r["time_ns"]) for r in rows]
    steps = [int(r["steps"]) for r in rows]
    smoothed_times = _moving_average(times, window)
    smoothed_steps = _moving_average(steps, window)

    # Теоретическая оценка: ~ log_m(N), где N — размер дерева на момент i.
    sizes = [max(tree_size_for_op(i), 1) for i in idx]
    theo_steps = [math.log(s, order) if s > 1 else 0 for s in sizes]
    # Подгонка коэффициента c так, чтобы средние совпадали: c = mean(steps)/mean(theo).
    mean_theo = sum(theo_steps) / max(len(theo_steps), 1)
    mean_steps = sum(steps) / max(len(steps), 1)
    c_steps = mean_steps / mean_theo if mean_theo > 0 else 1.0
    theo_steps_scaled = [t * c_steps for t in theo_steps]

    mean_time = sum(times) / max(len(times), 1)
    c_time = mean_time / mean_theo if mean_theo > 0 else 1.0
    theo_time_scaled = [t * c_time for t in theo_steps]

    ax_time.scatter(idx, times, s=2, alpha=0.15, color="C0", label="замер")
    ax_time.plot(idx, smoothed_times, color="C1", lw=1.5, label=f"скользящее (окно {window})")
    ax_time.plot(idx, theo_time_scaled, color="C3", lw=1.5, ls="--", label=f"теория c·log_{order}(N)")
    ax_time.set_title(f"{op_title}: время выполнения")
    ax_time.set_xlabel("номер операции")
    ax_time.set_ylabel("время, нс")
    ax_time.legend(loc="upper left", fontsize=8)
    ax_time.grid(True, alpha=0.3)

    ax_steps.scatter(idx, steps, s=2, alpha=0.15, color="C0", label="замер")
    ax_steps.plot(idx, smoothed_steps, color="C1", lw=1.5, label=f"скользящее (окно {window})")
    ax_steps.plot(idx, theo_steps_scaled, color="C3", lw=1.5, ls="--", label=f"теория c·log_{order}(N)")
    ax_steps.set_title(f"{op_title}: количество шагов")
    ax_steps.set_xlabel("номер операции")
    ax_steps.set_ylabel("число шагов")
    ax_steps.legend(loc="upper left", fontsize=8)
    ax_steps.grid(True, alpha=0.3)


def make_plots(order: int = DEFAULT_ORDER) -> None:
    insert_rows = _read_csv(os.path.join(RESULTS_DIR, "insert_metrics.csv"))
    search_rows = _read_csv(os.path.join(RESULTS_DIR, "search_metrics.csv"))
    delete_rows = _read_csv(os.path.join(RESULTS_DIR, "delete_metrics.csv"))

    n_total = len(insert_rows)

    # Размер дерева в момент i-й операции каждого типа.
    def insert_size(i: int) -> int:
        return i + 1

    def search_size(i: int) -> int:
        return n_total  # размер дерева константа на этапе поиска

    def delete_size(i: int) -> int:
        return n_total - i

    fig, ((a1, a2), (a3, a4), (a5, a6)) = plt.subplots(3, 2, figsize=(13, 11))
    _plot_op(a1, a2, insert_rows, "Вставка", order=order, window=WINDOW, tree_size_for_op=insert_size)
    _plot_op(a3, a4, search_rows, "Поиск",   order=order, window=SEARCH_WINDOW, tree_size_for_op=search_size)
    _plot_op(a5, a6, delete_rows, "Удаление", order=order, window=DELETE_WINDOW, tree_size_for_op=delete_size)
    fig.suptitle(f"B*-дерево, m={order}: практика vs теория", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97))

    combo_path = os.path.join(RESULTS_DIR, "combined.png")
    fig.savefig(combo_path, dpi=120)
    plt.close(fig)

    # Также сохраним отдельные PNG для удобства вставки в отчёт.
    for op_rows, op_name, op_title, win, size_fn in (
        (insert_rows, "insert", "Вставка", WINDOW, insert_size),
        (search_rows, "search", "Поиск", SEARCH_WINDOW, search_size),
        (delete_rows, "delete", "Удаление", DELETE_WINDOW, delete_size),
    ):
        fig, (at, asx) = plt.subplots(1, 2, figsize=(13, 4.2))
        _plot_op(at, asx, op_rows, op_title, order=order, window=win, tree_size_for_op=size_fn)
        fig.tight_layout()
        fig.savefig(os.path.join(RESULTS_DIR, f"{op_name}.png"), dpi=120)
        plt.close(fig)

    print("графики сохранены в", RESULTS_DIR)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--order", type=int, default=DEFAULT_ORDER)
    args = p.parse_args()
    make_plots(args.order)


if __name__ == "__main__":
    main()
