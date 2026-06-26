# Field of View and Density in Vicsek Flocking

An agent-based study of how a flock's forward field-of-view angle and its population density jointly shape the order-disorder phase transition.

## Full Research Report

The complete research report will be added to this repository at a later date.

## Overview

This project uses the Vicsek model of collective motion to ask how much an animal's limited field of view matters for the coherence of a flock, and whether that limitation can be offset by crowding more individuals together.

Each agent moves at constant speed and continuously turns to align its heading with the average heading of nearby neighbours. Two ingredients make the behaviour interesting. First, an agent only "sees" neighbours that fall inside a forward vision cone of angular width alpha, so a narrow cone discards information from behind. Second, a random perturbation (noise) of strength eta is added to every heading each step, fighting against alignment. As eta increases, the flock passes from coordinated motion (order) to a milling, uncorrelated state (disorder). This transition, and how its character is controlled by field of view and density, is the object of study.

The repository contains the headless simulation engine, the experimental sweep, the curve-fitting and statistical analysis, the figure generation, and an interactive Violet-based demo for inspecting the dynamics by eye.

## Research Question

How do field-of-view angle (alpha) and agent density (N) interact to shape the character of the order-disorder phase transition in a flock?

"Character" is split into two measurable properties of the transition:
- where it happens, captured by the critical noise level eta_c at which order collapses, and
- how sharply it happens, captured by the steepness k of the collapse.

## Method

### Model

The simulation is a Vicsek flocking model with a finite forward field of view, implemented as a vectorised NumPy update in [vicsek_core.py](vicsek_core.py). At each discrete step, every agent:

1. Finds its neighbours: other agents within an interaction radius r (using minimum-image periodic distances) that also lie inside its forward vision cone of half-angle alpha/2, measured from the agent's current heading. The agent always includes itself. When alpha is 360 degrees the cone test is skipped (omnidirectional vision).
2. Computes a new heading as the circular mean of its neighbours' headings, then adds angular noise drawn from a uniform distribution on (-eta/2, +eta/2).
3. Moves one step at constant speed v0 and wraps around the periodic (toroidal) world.

The degree of alignment is summarised by the order parameter phi, the magnitude of the mean heading vector. It ranges from 0 (completely disordered) to 1 (perfect alignment). For each run, phi is averaged over the post-burn-in frames.

Fixed parameters used throughout the sweep: world size L = 750, interaction radius r = 50, speed v0 = 2.0, 400 frames per run with the first 200 discarded as burn-in.

### Manipulated variables

- Field-of-view angle alpha: 90, 180, 270, 360 degrees.
- Agent density N: 50, 150, 300 agents in the fixed-size world.

### Control axis

- Noise eta: swept across 11 evenly spaced levels from 0.0 to 5.0, used to locate the transition for each (alpha, N) condition.

### Experimental design

A full factorial sweep of 4 field-of-view angles x 3 densities x 11 noise levels x 30 random seeds, giving 3,960 simulation runs. Per-run seeds are derived deterministically from (alpha, N, eta, replicate) via NumPy `SeedSequence`, so the entire sweep is reproducible. The sweep is driven by [sweep.py](sweep.py) and its raw output is written to [results.csv](results.csv) (one row per run: alpha, N, eta, seed, phi).

### Outcome metrics

For each (alpha, N, seed) the 11-point phi-vs-eta curve is fit with a logistic S-curve in [analysis.py](analysis.py):

```
phi(eta) = lo + (hi - lo) / (1 + exp(k * (eta - eta_c)))
```

Two quantities are extracted from each fit:
- steepness k, the logistic rate, describing how sharply order collapses (large k = abrupt, first-order-like collapse; small k = gradual, second-order-like decline), and
- break-point eta_c, the noise level at which the curve passes through its midpoint, marking where the transition occurs.

Per-curve fits are written to [fits.csv](fits.csv).

### Statistical test

A two-way ANOVA is run with alpha and N as categorical factors, with the primary test being the alpha x N interaction. The primary response is steepness k; a secondary ANOVA uses eta_c as the response to test where the transition sits. Both analyses are in [analysis.py](analysis.py) and use `statsmodels` ordinary-least-squares type-II ANOVA.

## Key Findings

Field of view and density interact to determine where the transition occurs (eta_c) but not how sharply it occurs (k).

- The break-point eta_c depends on the alpha x N interaction: a wider field of view and a higher density both push the collapse of order out to higher noise, and they do so jointly rather than independently. In the phi-vs-eta curves, wider cones (lighter lines) hold order to higher noise, and the spread between cones widens as density grows (see [fig1_curves.png](fig1_curves.png)).
- The steepness k does not show a meaningful alpha x N interaction. Transition sharpness is governed by density alone: collapse is abrupt at low density and becomes progressively more gradual as density rises, largely regardless of field of view (see [fig2_steepness.png](fig2_steepness.png) and the interaction plot [fig3_interaction.png](fig3_interaction.png)).
- Because sharpness tracks density and not the combination of density and vision, a higher density does not fully compensate for a narrow field of view.

The hypothesis was therefore only partly supported: the interaction shapes the location of the transition but not its sharpness.

Figure [fig4_metric.png](fig4_metric.png) illustrates the steepness metric itself, showing a fitted logistic with its break-point eta_c and maximum-slope tangent for a representative condition.

## Repository Structure

```
Vicsek-Fov-Density/
│
├── vicsek_core.py           # Headless, vectorised NumPy Vicsek model with FOV cone (run_sim)
├── sweep.py                 # Full factorial sweep -> results.csv
├── analysis.py              # Logistic fits + two-way ANOVA -> fits.csv, console tables
├── plots.py                 # Generates fig1..fig4 from results.csv and fits.csv
├── flocking_demo.py         # Interactive Violet/pygame demo (live, keyboard-controlled)
├── flocking.py              # Minimal Violet template
│
├── results.csv              # Raw sweep output (3,960 rows: alpha, N, eta, seed, phi)
├── fits.csv                 # Per-curve logistic fits (alpha, N, seed, k, eta_c, max_slope, r2)
│
├── fig1_curves.png          # phi vs eta, one panel per density, one curve per FOV
├── fig2_steepness.png       # Mean steepness k per condition (bars)
├── fig3_interaction.png     # FOV x density interaction plot for steepness
├── fig4_metric.png          # Worked example of the steepness metric
│
├── images/                  # Sprite images used by the Violet demo (triangle, green, etc.)
├── pyproject.toml           # Project metadata and dependencies
├── agent.jpynb
└── uv.lock                  # Locked dependency versions
```

## How to Run

The project targets Python 3.13+ and uses [uv](https://docs.astral.sh/uv/) for environment and dependency management. Dependencies (declared in [pyproject.toml](pyproject.toml)) are NumPy, pandas, SciPy, statsmodels, matplotlib, and violet-simulator.

Run each script from inside the `violet-starter-kit/` directory; the scripts read and write CSV and PNG files using relative paths.

Reproduce the full study end to end:

```sh
# 1. Run the full sweep (writes results.csv). This is the heavy step.
uv run sweep.py

# 2. Fit logistic curves and run the ANOVAs (writes fits.csv, prints tables).
uv run analysis.py

# 3. Generate the figures (writes fig1..fig4.png).
uv run plots.py
```

Note that `results.csv` and `fits.csv` are already included, so `analysis.py` and `plots.py` can be run directly without rerunning the sweep.

Quick timing probe of a single heaviest-condition run:

```sh
uv run vicsek_core.py
```

Interactive demo (opens a window; arrow keys adjust noise with up/down and field of view with left/right):

```sh
uv run flocking_demo.py
```

## Limitations

- Steepness is unreliable at low density. With few agents the phi-vs-eta curves are noisier and the logistic fits for k are correspondingly less stable, so the steepness estimates at N = 50 should be read with caution.
- Only intrinsic (angular) noise was tested. The model perturbs headings directly; vectorial or position-based noise, which can change the order of the transition, was not explored.
- The parameter ranges were narrow. Four field-of-view angles, three densities, and a single fixed combination of world size, radius, and speed cover only a small slice of the model's parameter space.
- Hysteresis was not measured. Noise was not ramped up and down, so any path dependence or bistability around the transition (a hallmark of a discontinuous transition) is not captured.
