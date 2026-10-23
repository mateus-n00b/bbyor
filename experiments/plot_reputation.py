#!/usr/bin/env python3
"""
Heatmap da evolução da reputação por nó (mesmo estilo da versão original).

    python3 experiments/plot_reputation.py reputation.csv [reputation.png] \
        [--peers sim/out/peers.json] [--bin 10]

Entrada: CSV de experiments/collect_reputation.py. Cada célula mostra a
reputação do nó ao final do intervalo; fica em branco até o nó ser sorteado
servidor pela primeira vez.
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


def load(path: pathlib.Path) -> list[dict]:
    with open(path) as f:
        rows = list(csv.DictReader(f))
    # Prefer the chain clock; fall back to collector time for old CSVs
    key = "block_time" if rows and "block_time" in rows[0] else "elapsed_s"
    t0 = min(float(r[key]) for r in rows)
    return sorted(
        ({"t": float(r[key]) - t0, "did": r["did"], "rep": float(r["reputation"])} for r in rows),
        key=lambda r: r["t"],
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


def build_matrix(rows, dids, bin_min):
    bin_s = bin_min * 60
    n_bins = int(rows[-1]["t"] // bin_s) + 1
    matrix = np.full((len(dids), n_bins), np.nan)
    index = {d: i for i, d in enumerate(dids)}
    current = {}
    it = iter(rows)
    row = next(it, None)
    for b in range(n_bins):
        end = (b + 1) * bin_s
        while row is not None and row["t"] < end:
            current[row["did"]] = row["rep"]
            row = next(it, None)
        for did, rep in current.items():
            if did in index:
                matrix[index[did], b] = rep
    return matrix


def plot(matrix, bin_min, output: pathlib.Path):
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
    ax.set_xticklabels([fmt_minutes(b * bin_min) for b in range(n_bins)], rotation=45, fontsize=10)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_xlabel(f"Reputation evolution ({bin_min:g}min intervals)", fontsize=14)
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
    parser.add_argument("--bin", type=float, default=10, help="tamanho do intervalo em minutos (padrão 10)")
    args = parser.parse_args()

    rows = load(args.csv)
    if not rows:
        raise SystemExit("CSV sem rodadas finalizadas")
    dids = node_order(rows, args.peers)
    plot(build_matrix(rows, dids, args.bin), args.bin, args.output)


if __name__ == "__main__":
    main()
