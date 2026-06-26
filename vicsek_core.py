"""
Vicsek flocking model with a finite field-of-view (FOV) cone.
Headless, vectorised NumPy implementation. Identical dynamics to the Violet
version used for the live demo; this one is built for speed/reproducibility.

Update rule (intrinsic / angular noise), per discrete step:
  1. neighbours = agents within radius r (periodic distance) AND inside the
     FOV cone of half-angle alpha/2 measured from the agent's heading.
     The agent always includes itself.
  2. new heading = atan2( mean sin(theta_j), mean cos(theta_j) ) + noise
     noise ~ Uniform(-eta/2, +eta/2)
  3. move at constant speed v0, wrap with periodic boundaries.

Order parameter:  phi = | (1/N) sum_j (cos theta_j, sin theta_j) |  in [0,1].
"""
import numpy as np


def run_sim(N, L, r, v0, alpha_deg, eta, n_frames, burn_in, seed):
    rng = np.random.default_rng(seed)
    pos = rng.uniform(0.0, L, size=(N, 2))
    theta = rng.uniform(-np.pi, np.pi, size=N)

    half_fov = np.deg2rad(alpha_deg) / 2.0
    cos_half = np.cos(half_fov)   # visible if cos(angle_to_neighbour) >= cos_half
    r2 = r * r

    phis = []
    for t in range(n_frames):
        # displacement j - i with minimum-image periodic convention
        dx = pos[:, 0][None, :] - pos[:, 0][:, None]
        dy = pos[:, 1][None, :] - pos[:, 1][:, None]
        dx -= L * np.round(dx / L)
        dy -= L * np.round(dy / L)
        dist2 = dx * dx + dy * dy

        within = dist2 <= r2                      # inside interaction radius
        if alpha_deg >= 360:
            mask = within.astype(np.float64)      # omnidirectional: no cone test
        else:
            hx = np.cos(theta)[:, None]           # heading unit vector of i
            hy = np.sin(theta)[:, None]
            dot = hx * dx + hy * dy               # dot(heading_i, (i->j))
            # angle <= alpha/2  <=>  dot >= cos(alpha/2)*|i->j|
            visible = dot >= cos_half * np.sqrt(dist2)
            mask = (within & visible).astype(np.float64)
        np.fill_diagonal(mask, 1.0)               # always include self

        sum_cos = mask @ np.cos(theta)
        sum_sin = mask @ np.sin(theta)
        avg_theta = np.arctan2(sum_sin, sum_cos)

        noise = eta * (rng.random(N) - 0.5)       # Uniform(-eta/2, eta/2)
        theta = avg_theta + noise

        pos[:, 0] = (pos[:, 0] + v0 * np.cos(theta)) % L
        pos[:, 1] = (pos[:, 1] + v0 * np.sin(theta)) % L

        if t >= burn_in:
            phis.append(np.hypot(np.cos(theta).mean(), np.sin(theta).mean()))

    return float(np.mean(phis))


if __name__ == "__main__":
    import time
    # timing probe on the heaviest condition
    t0 = time.time()
    p = run_sim(N=300, L=750, r=50, v0=2.0, alpha_deg=360, eta=1.0,
                n_frames=400, burn_in=200, seed=0)
    dt = time.time() - t0
    print(f"single N=300 run: phi={p:.3f}  time={dt:.2f}s")
