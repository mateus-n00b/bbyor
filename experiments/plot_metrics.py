#!/usr/bin/env python3
"""
Plota métricas BBYOR com intervalo de confiança de 95%.

Modo simples (apenas FHE+ZKP):
    python3 plot_metrics.py metrics_all.jsonl [output.png]

Modo comparação (FHE+ZKP vs Baseline):
    python3 plot_metrics.py metrics_all.jsonl --baseline metrics_baseline.jsonl [output.png]
"""

import sys
import json
import argparse
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats

# ---------------------------------------------------------------------------
# Operações e metadados
# ---------------------------------------------------------------------------

# Operation names recorded by node/bbyor/node.py
FHE_OPS = [
    "challenge_create",
    "zk_commit",
    "chain_commit",
    "challenge_respond",
    "zk_prove",
    "chain_submit_proof",
    "answer_total",
]

BASELINE_OPS = [
    "challenge_create",
    "challenge_respond",
    "sig_sign",
    "sig_verify",
    "answer_total",
]

LABELS_FHE = {
    "challenge_create":   "Criação Desafio\n(Servidor)",
    "zk_commit":          "Commitment\nPoseidon",
    "chain_commit":       "Tx commit\n(on-chain)",
    "challenge_respond":  "Resposta FHE\n(Verificador)",
    "zk_prove":           "ZKP Prove\n(Groth16)",
    "chain_submit_proof": "Tx submitProof\n(verificação on-chain)",
    "answer_total":       "Total\n(Verificador)",
}

# Grupos para o gráfico de comparação: (label_grupo, op_fhe, op_baseline)
COMPARISON_GROUPS = [
    ("Criação\n(Servidor)",       "challenge_create",   "challenge_create"),
    ("Cômputo\n(Verificador)",    "challenge_respond",  "challenge_respond"),
    ("Prova /\nAssinatura",       "zk_prove",           "sig_sign"),
    ("Verificação",               "chain_submit_proof", "sig_verify"),
    ("Total\n(Verificador)",      "answer_total",       "answer_total"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_samples(path: pathlib.Path, ops: list) -> dict:
    samples = {op: [] for op in ops}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            op = entry.get("operation")
            if op in samples:
                samples[op].append(entry["duration_ms"])
    return samples


def compute_ci(data: np.ndarray):
    n = len(data)
    mean = data.mean()
    ci = stats.t.ppf(0.975, df=n - 1) * stats.sem(data)
    return mean, ci, n


def annotate_bars(ax, bars, means, ci_half, ns, max_val):
    for rect, mean, ci, n in zip(bars, means, ci_half, ns):
        top = rect.get_height() + ci
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            top + max_val * 0.015,
            f"{mean:.1f}\n(n={n})",
            ha="center", va="bottom", fontsize=7.5, color="#222222",
        )


# ---------------------------------------------------------------------------
# Modo simples — apenas FHE+ZKP
# ---------------------------------------------------------------------------

def plot_single(fhe_file: pathlib.Path, output: pathlib.Path):
    samples = load_samples(fhe_file, FHE_OPS)
    available = [op for op in FHE_OPS if len(samples[op]) >= 2]
    if not available:
        print("Nenhuma operação com dados suficientes encontrada.")
        sys.exit(1)

    print("\n=== FHE + ZKP ===")
    means, ci_half, ns = [], [], []
    for op in available:
        mean, ci, n = compute_ci(np.array(samples[op]))
        means.append(mean)
        ci_half.append(ci)
        ns.append(n)
        print(f"  {op:40s}  n={n:4d}  mean={mean:9.2f} ms  ±{ci:.2f} ms (95% IC)")

    x = np.arange(len(available))
    bar_width = 0.55
    colors = plt.cm.tab10(np.linspace(0, 0.6, len(available)))

    fig, ax = plt.subplots(figsize=(max(9, len(available) * 1.6), 5))
    bars = ax.bar(
        x, means, bar_width,
        yerr=ci_half, capsize=6,
        color=colors, edgecolor="white", linewidth=0.8,
        error_kw={"elinewidth": 1.5, "ecolor": "#333333", "capthick": 1.5},
    )

    max_val = max(m + c for m, c in zip(means, ci_half))
    annotate_bars(ax, bars, means, ci_half, ns, max_val)

    ax.set_xticks(x)
    ax.set_xticklabels([LABELS_FHE.get(op, op) for op in available], fontsize=10)
    ax.set_ylabel("Tempo de processamento (ms)", fontsize=11)
    ax.set_title("Latência das operações BBYOR (FHE + ZKP) — IC 95%", fontsize=13, pad=14)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylim(0, max_val * 1.20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"\nGráfico salvo em: {output}")
    plt.show()


# ---------------------------------------------------------------------------
# Modo comparação — FHE+ZKP vs Baseline
# ---------------------------------------------------------------------------

def plot_comparison(fhe_file: pathlib.Path, baseline_file: pathlib.Path, output: pathlib.Path):
    fhe_samples = load_samples(fhe_file, FHE_OPS)
    bl_samples  = load_samples(baseline_file, BASELINE_OPS)

    bar_width = 0.35
    fhe_means, fhe_ci, fhe_ns = [], [], []
    bl_means,  bl_ci,  bl_ns  = [], [], []
    group_labels = []

    print("\n=== FHE + ZKP  vs  Baseline (plain + ECDSA secp256k1) ===")
    for label, op_fhe, op_bl in COMPARISON_GROUPS:
        d_fhe = np.array(fhe_samples.get(op_fhe, []))
        d_bl  = np.array(bl_samples.get(op_bl, []))
        if len(d_fhe) < 2 or len(d_bl) < 2:
            print(f"  [aviso] Dados insuficientes para '{label.replace(chr(10), ' ')}' "
                  f"(fhe n={len(d_fhe)}, baseline n={len(d_bl)}) — grupo omitido.")
            continue

        m_fhe, c_fhe, n_fhe = compute_ci(d_fhe)
        m_bl,  c_bl,  n_bl  = compute_ci(d_bl)

        fhe_means.append(m_fhe); fhe_ci.append(c_fhe); fhe_ns.append(n_fhe)
        bl_means.append(m_bl);   bl_ci.append(c_bl);   bl_ns.append(n_bl)
        group_labels.append(label)

        print(f"  {op_fhe:40s}  n={n_fhe:4d}  mean={m_fhe:9.3f} ms  ±{c_fhe:.3f} ms")
        print(f"  {op_bl:40s}  n={n_bl:4d}  mean={m_bl:9.3f} ms  ±{c_bl:.3f} ms")

    if not group_labels:
        print("Nenhum grupo com dados suficientes.")
        sys.exit(1)

    x = np.arange(len(group_labels))
    fig, ax = plt.subplots(figsize=(max(9, len(group_labels) * 2.4), 6))

    bars_fhe = ax.bar(
        x - bar_width / 2, fhe_means, bar_width,
        yerr=fhe_ci, capsize=5,
        color="#4C72B0", edgecolor="white", linewidth=0.8,
        label="FHE + ZKP (Groth16)",
        error_kw={"elinewidth": 1.4, "ecolor": "#333333", "capthick": 1.4},
    )
    bars_bl = ax.bar(
        x + bar_width / 2, bl_means, bar_width,
        yerr=bl_ci, capsize=5,
        color="#DD8452", edgecolor="white", linewidth=0.8,
        label="Baseline (plain + ECDSA secp256k1)",
        error_kw={"elinewidth": 1.4, "ecolor": "#333333", "capthick": 1.4},
    )

    all_tops = [m + c for m, c in zip(fhe_means + bl_means, fhe_ci + bl_ci)]
    max_val = max(all_tops)

    annotate_bars(ax, bars_fhe, fhe_means, fhe_ci, fhe_ns, max_val)
    annotate_bars(ax, bars_bl,  bl_means,  bl_ci,  bl_ns,  max_val)

    ax.set_xticks(x)
    ax.set_xticklabels(group_labels, fontsize=10)
    ax.set_ylabel("Tempo de processamento (ms)", fontsize=11)
    ax.set_title("BBYOR: FHE+ZKP vs Baseline criptográfico — IC 95%", fontsize=13, pad=14)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.1f}"))
    ax.set_ylim(0, max_val * 1.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(fontsize=10, framealpha=0.85)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"\nGráfico salvo em: {output}")
    plt.show()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "fhe_file", type=pathlib.Path,
        help="JSONL com métricas FHE+ZKP (ex: metrics_all.jsonl)",
    )
    parser.add_argument(
        "--baseline", type=pathlib.Path, metavar="BASELINE_FILE",
        help="JSONL com métricas baseline para gráfico comparativo",
    )
    parser.add_argument(
        "output", nargs="?", type=pathlib.Path,
        default=pathlib.Path("metrics_plot.png"),
        help="Arquivo de saída PNG (default: metrics_plot.png)",
    )
    args = parser.parse_args()

    if args.baseline:
        plot_comparison(args.fhe_file, args.baseline, args.output)
    else:
        plot_single(args.fhe_file, args.output)


if __name__ == "__main__":
    main()
