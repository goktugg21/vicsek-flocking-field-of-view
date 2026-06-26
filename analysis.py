"""
A4 analysis: fit a logistic to each phi-vs-eta curve, extract steepness,
then run the two-way ANOVA that tests the FOV x density interaction.

Reads:  results.csv   (columns: alpha, N, eta, seed, phi)   <- 30-seed sweep
Writes: fits.csv      (one row per alpha x N x seed)
Prints: fit quality, steepness summary, and BOTH ANOVA tables + residual df.

Metric definition (UNCHANGED from A3, so A3 -> A4 is a clean extension):
  logistic:  phi(eta) = lo + (hi - lo) / (1 + exp(k*(eta - eta_c)))
  STEEPNESS = k   (units 1/noise).  large k -> sharp collapse (first-order-like);
                                    small k -> gradual decline (second-order-like).
  max_slope = k*(hi-lo)/4  is |dphi/deta| at the inflection point eta_c.

Only the seed COUNT changed (10 -> 30). Model, bounds and columns are identical,
so the two weeks are directly comparable.
"""
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import statsmodels.api as sm
from statsmodels.formula.api import ols

df = pd.read_csv("results.csv")

ALPHAS = sorted(df["alpha"].unique())
NS     = sorted(df["N"].unique())
SEEDS  = sorted(df["seed"].unique())
N_EXPECTED = len(ALPHAS) * len(NS) * len(SEEDS)   # 4 x 3 x 30 = 360 curves


def logistic(eta, lo, hi, k, ec):
    return lo + (hi - lo) / (1.0 + np.exp(k * (eta - ec)))


fits = []
for (alpha, N, seed), g in df.groupby(["alpha", "N", "seed"]):
    g = g.sort_values("eta")
    x, y = g["eta"].values, g["phi"].values
    p0 = [y.min(), y.max(), 2.0,
          x[np.argmin(np.abs(y - (y.min() + y.max()) / 2))]]
    bounds = ([0.0, 0.3, 0.05, 0.0], [0.4, 1.05, 60.0, 5.0])
    try:
        popt, _ = curve_fit(logistic, x, y, p0=p0, bounds=bounds, maxfev=20000)
        lo, hi, k, ec = popt
        yhat = logistic(x, *popt)
        ss_res = float(np.sum((y - yhat) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
        max_slope = k * (hi - lo) / 4.0
        fits.append((alpha, N, seed, k, ec, max_slope, r2))
    except Exception:
        fits.append((alpha, N, seed, np.nan, np.nan, np.nan, np.nan))

fit = pd.DataFrame(fits, columns=["alpha", "N", "seed", "steepness_k",
                                  "eta_c", "max_slope", "r2"])
fit.to_csv("fits.csv", index=False)

n_ok = int(fit["steepness_k"].notna().sum())
print("=== FIT QUALITY ===")
print(f"curves fitted: {n_ok}/{N_EXPECTED}   (dropped: {N_EXPECTED - n_ok})")
print(f"median R^2: {fit['r2'].median():.3f}    min R^2: {fit['r2'].min():.3f}")

print(f"\n=== STEEPNESS (k) BY CONDITION  [mean +/- sd over {len(SEEDS)} seeds] ===")
summary = fit.groupby(["alpha", "N"])["steepness_k"].agg(["mean", "std"]).round(3)
print(summary)

clean = fit.dropna()

print("\n=== PRIMARY  TWO-WAY ANOVA:  steepness_k ~ C(alpha) * C(N) ===")
model = ols("steepness_k ~ C(alpha) * C(N)", data=clean).fit()
print(sm.stats.anova_lm(model, typ=2).round(4))
print(f"residual df = {int(model.df_resid)}   <-- report THIS exact number")

print("\n=== SECONDARY  ANOVA:  eta_c ~ C(alpha) * C(N)  (transition location) ===")
model2 = ols("eta_c ~ C(alpha) * C(N)", data=clean).fit()
print(sm.stats.anova_lm(model2, typ=2).round(4))
print(f"residual df = {int(model2.df_resid)}")
