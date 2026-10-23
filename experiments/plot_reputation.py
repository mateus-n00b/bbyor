#!/usr/bin/env python3
"""
Heatmap da evolução da reputação por nó (mesmo estilo da versão original).

    python3 experiments/plot_reputation.py reputation.csv [reputation.png] \
        [--peers sim/out/peers.json] [--x rounds|time] [--bin N]

Entrada: CSV de experiments/collect_reputation.py. O eixo x é por rodadas
(padrão: blocos de 20 rodadas) ou por tempo (--x time, blocos de 10 min).
Cada célula mostra a reputação do nó ao final do bloco; fica em branco até o
nó ser sorteado servidor pela primeira vez.
"""

import argparse
import csv
import json
import pathlib

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Amarelo -> laranja -> vermelho, como no heatmap original
CMAP = LinearSegmentedColormap.from_list("reputation", ["#FFFF00", "#FFC000", "#FF8C00", "#CC0000"])
CMAP.set_bad("white")


def load(path: pathlib.Path, axis: str) -> list[dict]:
    """Returns rows sorted by x: the round number, or seconds since the first round."""
    with open(path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []
    if axis == "rounds":
        xs = [int(r["round"]) for r in rows]
    else:
        # Prefer the chain clock; fall back to collector time for old CSVs
        key = "block_time" if "block_time" in rows[0] else "elapsed_s"
        t0 = min(float(r[key]) for r in rows)
        xs = [float(r[key]) - t0 for r in rows]
    return sorted(
        ({"x": x, "did": r["did"], "rep": float(r["reputation"])} for x, r in zip(xs, rows)),
        key=lambda r: r["x"],
    )


def node_order(rows: list[dict], peers: pathlib.Path | None) -> list[str]:
    if peers:
        # Node #i is node(i-1) of the generated compose
        return [p["did"] for p in json.loads(peers.read_text())]
    seen = []
    for r in rows:
        if r["did"] not in seen:
            seen.append(r["did"])
    return seen


def fmt_minutes(m: float) -> str:
    h, rest = divmod(int(m), 60)
    return f"{rest}min" if h == 0 else f"{h}h{rest:02d}min"


def bin_of(x, axis: str, size: float) -> int:
    # Round blocks are 1..size, size+1..2*size, ...; time blocks start at 0
    return int((x - 1) // size) if axis == "rounds" else int(x // (size * 60))


def bin_label(b: int, axis: str, size: float) -> str:
    return f"{int((b + 1) * size)}" if axis == "rounds" else fmt_minutes(b * size)


def build_matrix(rows, dids, axis, size):
    n_bins = bin_of(rows[-1]["x"], axis, size) + 1
    matrix = np.full((len(dids), n_bins), np.nan)
    index = {d: i for i, d in enumerate(dids)}
    current = {}
    it = iter(rows)
    row = next(it, None)
    for b in range(n_bins):
        while row is not None and bin_of(row["x"], axis, size) <= b:
            current[row["did"]] = row["rep"]
            row = next(it, None)
        for did, rep in current.items():
            if did in index:
                matrix[index[did], b] = rep
    return matrix


def plot(matrix, axis, size, output: pathlib.Path):
    n_nodes, n_bins = matrix.shape
    fig, ax = plt.subplots(figsize=(max(8, 0.6 * n_bins + 2), max(4, 0.36 * n_nodes + 1.2)))
    mesh = ax.pcolormesh(
        np.ma.masked_invalid(matrix), cmap=CMAP, vmin=0, vmax=1,
        edgecolors="gray", linewidth=1,
    )
    ax.invert_yaxis()
    ax.set_yticks(np.arange(n_nodes) + 0.5)
    ax.set_yticklabels([f"Node #{i + 1}" for i in range(n_nodes)], fontsize=12)
    ax.set_xticks(np.arange(n_bins) + 0.5)
    ax.set_xticklabels([bin_label(b, axis, size) for b in range(n_bins)], rotation=45, fontsize=10)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    if axis == "rounds":
        ax.set_xlabel(f"Reputation evolution (rounds, {size:g}-round intervals)", fontsize=14)
    else:
        ax.set_xlabel(f"Reputation evolution ({size:g}min intervals)", fontsize=14)
    ax.set_ylabel("Nodes", fontsize=14)

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Reputation (%)", fontsize=14)
    cbar.outline.set_visible(False)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Gráfico salvo em: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", type=pathlib.Path, help="saída de collect_reputation.py")
    parser.add_argument("output", nargs="?", type=pathlib.Path, default=pathlib.Path("reputation.png"))
    parser.add_argument("--peers", type=pathlib.Path,
                        help="peers.json do cenário: ordena as linhas como node0..nodeN")
    parser.add_argument("--x", choices=["rounds", "time"], default="rounds", help="eixo x (padrão: rounds)")
    parser.add_argument("--bin", type=float,
                        help="tamanho do bloco: rodadas (padrão 20) ou minutos com --x time (padrão 10)")
    args = parser.parse_args()
    size = args.bin or (20 if args.x == "rounds" else 10)

    rows = load(args.csv, args.x)
    if not rows:
        raise SystemExit("CSV sem rodadas finalizadas")
    dids = node_order(rows, args.peers)
    plot(build_matrix(rows, dids, args.x, size), args.x, size, args.output)


if __name__ == "__main__":
    main()
