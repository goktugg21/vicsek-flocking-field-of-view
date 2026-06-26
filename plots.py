"""
A4 figures. Reads results.csv (raw) and fits.csv (from analysis.py).
All error bars span the seeds. Set ERROR below to switch SD <-> SEM.

Produces:
  fig1_curves.png       phi vs eta, one panel per density, 4 FOV curves, +/- error band
  fig2_steepness.png    mean steepness k per condition (bars + error bars)
  fig3_interaction.png  FOV x density interaction plot (mean k, one line per alpha)
  fig4_metric.png       what "steepness" means: a fitted logistic + max-slope tangent

Run AFTER analysis.py (it needs fits.csv).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

ERROR = "sem"    # SEM = SD/sqrt(30): ~5.5x smaller bars. "sd" = wider spread across seeds.
ELABEL = {"sd": "SD", "sem": "SEM"}[ERROR]

res = pd.read_csv("results.csv")
fit = pd.read_csv("fits.csv").dropna()

ALPHAS  = sorted(res["alpha"].unique())
NS      = sorted(res["N"].unique())
N_SEEDS = res["seed"].nunique()
COLORS  = plt.cm.viridis(np.linspace(0.1, 0.85, len(ALPHAS)))


def err(std, n):
    return std / np.sqrt(n) if ERROR == "sem" else std


# ---- fig1: phi vs eta curves -------------------------------------------------
g = (res.groupby(["alpha", "N", "eta"])["phi"]
        .agg(["mean", "std"]).reset_index())
fig, axes = plt.subplots(1, len(NS), figsize=(5 * len(NS), 4.2), sharey=True)
if len(NS) == 1:
    axes = [axes]
for ax, N in zip(axes, NS):
    for c, alpha in zip(COLORS, ALPHAS):
        d = g[(g["N"] == N) & (g["alpha"] == alpha)].sort_values("eta")
        ax.errorbar(d["eta"], d["mean"], yerr=err(d["std"].values, N_SEEDS),
                    marker="o", ms=3, lw=1.5, capsize=2, color=c,
                    label=f"\u03b1={int(alpha)}\u00b0")
    ax.set_title(f"N = {N}")
    ax.set_xlabel("noise \u03b7")
    ax.grid(alpha=.3)
axes[0].set_ylabel("polarisation \u03c6")
axes[0].legend(title="FOV", fontsize=8)
fig.suptitle(f"\u03c6 vs \u03b7 across FOV and density  "
             f"(mean \u00b1 {ELABEL}, {N_SEEDS} seeds)", fontsize=12)
fig.tight_layout()
fig.savefig("fig1_curves.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- fig2: steepness k by condition -----------------------------------------
s = fit.groupby(["alpha", "N"])["steepness_k"].agg(["mean", "std"]).reset_index()
fig, ax = plt.subplots(figsize=(7.5, 4.5))
width = 0.8 / len(ALPHAS)
xN = np.arange(len(NS))
for i, (c, alpha) in enumerate(zip(COLORS, ALPHAS)):
    d = s[s["alpha"] == alpha].set_index("N").reindex(NS)
    ax.bar(xN + i * width, d["mean"].values, width,
           yerr=err(d["std"].values, N_SEEDS), capsize=3, color=c,
           label=f"\u03b1={int(alpha)}\u00b0")
ax.set_xticks(xN + width * (len(ALPHAS) - 1) / 2)
ax.set_xticklabels([f"N={n}" for n in NS])
ax.set_ylabel("steepness  k  (1/noise)")
ax.set_title(f"Transition steepness by condition "
             f"(mean \u00b1 {ELABEL}, {N_SEEDS} seeds)")
ax.legend(title="FOV", fontsize=8)
ax.grid(axis="y", alpha=.3)
fig.tight_layout()
fig.savefig("fig2_steepness.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- fig3: interaction plot --------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 4.5))
for c, alpha in zip(COLORS, ALPHAS):
    d = s[s["alpha"] == alpha].set_index("N").reindex(NS)
    ax.errorbar(NS, d["mean"].values, yerr=err(d["std"].values, N_SEEDS),
                marker="o", lw=1.8, capsize=3, color=c,
                label=f"\u03b1={int(alpha)}\u00b0")
ax.set_xlabel("density  N")
ax.set_ylabel("mean steepness  k")
ax.set_title("FOV \u00d7 density interaction\n(non-parallel lines = interaction)")
ax.set_xticks(NS)
ax.legend(title="FOV", fontsize=8)
ax.grid(alpha=.3)
fig.tight_layout()
fig.savefig("fig3_interaction.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---- fig4: what 'steepness' means -------------------------------------------
def logistic(eta, lo, hi, k, ec):
    return lo + (hi - lo) / (1.0 + np.exp(k * (eta - ec)))

aE, nE = ALPHAS[-1], NS[-1]          # representative: widest FOV, highest density
d = (res[(res["alpha"] == aE) & (res["N"] == nE)]
        .groupby("eta")["phi"].mean().reset_index().sort_values("eta"))
x, y = d["eta"].values, d["phi"].values
p0 = [y.min(), y.max(), 2.0, x[np.argmin(np.abs(y - (y.min() + y.max()) / 2))]]
popt, _ = curve_fit(logistic, x, y, p0=p0,
                    bounds=([0, 0.3, 0.05, 0], [0.4, 1.05, 60, 5]), maxfev=20000)
lo, hi, k, ec = popt
xx = np.linspace(x.min(), x.max(), 300)
fig, ax = plt.subplots(figsize=(6.5, 4.5))
ax.scatter(x, y, s=25, color="#444", zorder=3, label="data (seed-mean \u03c6)")
ax.plot(xx, logistic(xx, *popt), color="#C0522A", lw=2, label="fitted logistic")
slope = -k * (hi - lo) / 4.0          # signed slope at inflection (curve descends)
phi_c = lo + (hi - lo) / 2.0
tx = np.linspace(ec - 0.9, ec + 0.9, 2)
ax.plot(tx, phi_c + slope * (tx - ec), "--", color="#1f6f8b", lw=1.6,
        label=f"max slope |d\u03c6/d\u03b7| = {abs(slope):.2f}")
ax.axvline(ec, color="grey", ls=":", lw=1)
ax.annotate(f"\u03b7_c = {ec:.2f}", (ec, lo + 0.03), fontsize=9, color="grey")
ax.set_xlabel("noise \u03b7")
ax.set_ylabel("polarisation \u03c6")
ax.set_title(f"Steepness k = logistic rate  (\u03b1={int(aE)}\u00b0, N={nE})")
ax.legend(fontsize=8)
ax.grid(alpha=.3)
fig.tight_layout()
fig.savefig("fig4_metric.png", dpi=150, bbox_inches="tight")
plt.close(fig)

print(f"saved fig1..fig4 with {ELABEL} error bars ({N_SEEDS} seeds)")
