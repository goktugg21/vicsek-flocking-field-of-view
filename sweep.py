"""Full headless sweep: 4 FOV angles x 3 densities x 11 noise levels x 10 seeds."""
import time
import numpy as np
import pandas as pd
from vicsek_core import run_sim

L, R, V0 = 750, 50, 2.0
N_FRAMES, BURN_IN = 400, 200

ALPHAS = [90, 180, 270, 360]      # FOV angle (degrees)
NS = [50, 150, 300]               # population / density
ETAS = np.round(np.linspace(0.0, 5.0, 11), 2)   # noise levels
SEEDS = list(range(30))           # replicates per condition

rows = []
total = len(ALPHAS) * len(NS) * len(ETAS) * len(SEEDS)
done = 0
t0 = time.time()
for alpha in ALPHAS:
    for N in NS:
        for eta in ETAS:
            for rep in SEEDS:
                # fully reproducible per-run seed
                ss = np.random.SeedSequence([alpha, N, int(eta * 100), rep])
                seed = int(ss.generate_state(1)[0])
                phi = run_sim(N, L, R, V0, alpha, float(eta),
                              N_FRAMES, BURN_IN, seed)
                rows.append((alpha, N, float(eta), rep, phi))
                done += 1
        print(f"  alpha={alpha:3d} N={N:3d} done  "
              f"[{done}/{total}]  {time.time()-t0:.0f}s")

df = pd.DataFrame(rows, columns=["alpha", "N", "eta", "seed", "phi"])
df.to_csv("results.csv", index=False)
print(f"\nSaved results.csv  ({len(df)} rows)  total {time.time()-t0:.0f}s")
