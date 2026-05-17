"""
post_process.py

Post-processing script for unsteady wing surface probe data.

Run this from the unsteady run directory with::

    python postprocessing/post_process.py

Prerequisites:
    1. pvpython ./postprocessing/extract_normals_area.py
       (extracts normals, area, p_force, pstat, ro, rovx, ..., x, y, z
        from probe_out.xdmf at all timesteps)

What it does
------------
1. Loads the pre-extracted .npy arrays from ./post-processing/
    NB, ./post-processing/ contains the probed data for the
    WING SURFACE, not the y=constant probes
2. Computes lift coefficient C_L and root bending moment coefficient
3. Plots C_L and BM time histories
4. Saves C_L and normalised root BM as .npy files

No ParaView dependency — runs with plain Python.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

from ts_utils.pv_utils import (
    compute_lift_coefficient,
    compute_root_bending_moment,
    normalise_bending_moment,
    plot_series,
)

# =============================================================================
# CONFIG — edit per case
# =============================================================================
POST_DIR = './post-processing'

# Flow conditions / wing reference geometry
Q       = 5500.0    # dynamic pressure  [Pa]
S       = 154.0     # reference area    [m^2] (one wing, as CFD models one wing)
C_MEAN  = 6.535     # mean aerodynamic chord [m]

# Output filenames
CASE_TAG    = 'm0650_q5500_aoa4_H200'
CL_OUTFILE  = os.path.join(POST_DIR, f'C_L_{CASE_TAG}.npy')
BM_OUTFILE  = os.path.join(POST_DIR, f'rootBM_{CASE_TAG}.npy')

# Matplotlib font sizes
plt.rcParams.update({
    'font.size': 18,
    'axes.titlesize': 24,
    'axes.labelsize': 22,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
})

# =============================================================================
# 1. Load pre-extracted arrays
# =============================================================================
# These are saved by extract_normals_area.py which runs the full ParaView
# pipeline (all wing probes selected at once) and loops over all timesteps.
print('Loading pre-extracted arrays from', POST_DIR)

p_force = np.load(os.path.join(POST_DIR, 'p_force.npy'))  # (nt, nn, 3)
y_raw   = np.load(os.path.join(POST_DIR, 'y.npy'))        # (nn,) or (nt, nn)

# y may be (nt, nn) if extracted at all timesteps, or (nn,) if static.
# Either way, the geometry is static so take first timestep if needed.
if y_raw.ndim == 2:
    y = y_raw[0]
else:
    y = y_raw

nt, nn, _ = p_force.shape
print(f'  p_force: {p_force.shape}  (nt={nt}, nn={nn})')
print(f'  y:       {y.shape}')

# =============================================================================
# 2. Compute C_L and BM (or load from cache if already computed)
# =============================================================================
if os.path.exists(CL_OUTFILE) and os.path.exists(BM_OUTFILE):
    print(f'\nLoading cached results from {CL_OUTFILE} and {BM_OUTFILE}')
    C_L     = np.load(CL_OUTFILE)
    BM_norm = np.load(BM_OUTFILE)
else:
    # C_L from the z-component of total pressure force (lift direction = z)
    C_L = compute_lift_coefficient(p_force, q=Q, S=S, lift_axis=2)

    # Bending moment about the wing root (minimum y location)
    BM      = compute_root_bending_moment(p_force, y)   # (nt, 3)
    BM_mag  = np.linalg.norm(BM, axis=1)                # (nt,)
    BM_norm = normalise_bending_moment(BM_mag, q=Q, S=S, c_mean=C_MEAN)

    # Save
    np.save(CL_OUTFILE, C_L)
    np.save(BM_OUTFILE, BM_norm)
    print(f'\nSaved {CL_OUTFILE}')
    print(f'Saved {BM_OUTFILE}')

print(f'  C_L range: [{C_L.min():.4f}, {C_L.max():.4f}],  mean: {C_L.mean():.4f}')
print(f'  BM_norm range: [{BM_norm.min():.4f}, {BM_norm.max():.4f}],  mean: {BM_norm.mean():.4f}')

# =============================================================================
# 3. Plots
# =============================================================================
# Read gust gradient H from gust_config.ofp for legend labels
GUST_CONFIG = './gust_config.ofp'
with open(GUST_CONFIG) as f:
    for line in f:
        if line.startswith('H'):
            H_gust = int(line.split('=')[1].strip())
            break
GUST_LABEL = f'H = {H_gust} ft'

# Change relative to steady state (timestep 0) to isolate gust effect
dC_L    = C_L - C_L[0]
dBM_norm = -BM_norm - (-BM_norm[0])

plot_series(dC_L, ylabel=r'$\Delta C_L$', title='Change in lift', label=GUST_LABEL, show=False)
plt.savefig(os.path.join(POST_DIR, f'C_L_{CASE_TAG}.png'), dpi=150, bbox_inches='tight')
print(f'Saved C_L plot')

# Negate BM for plotting: convention is sagging moment = negative
plot_series(dBM_norm, ylabel=r'$\Delta C_{M,root}$', title='Change in root bending moment', label=GUST_LABEL, show=False)
plt.savefig(os.path.join(POST_DIR, f'rootBM_{CASE_TAG}.png'), dpi=150, bbox_inches='tight')
print(f'Saved root BM plot')
