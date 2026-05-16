"""
post_process.py

Example post-processing script using the ``pv_utils`` package.

Run this from the unsteady run directory with::

    pvpython postprocessing/post_process.py

What it does
------------
1.  Reads ``probe_out.xdmf`` via ParaView and recovers the per-point
    ``Normals`` and ``Area`` arrays for the wing surface probe.
2.  Loads the previously-saved ``.npy`` probe arrays (ro, rovx, ..., x, y, z).
3.  Computes pstat, the per-node pressure force vector, the total lift
    coefficient, and the root bending moment time history.
4.  Plots a pressure time-series at a chosen target station, plus the
    C_L and root BM histories.
5.  Saves the C_L and normalised root BM as ``.npy`` files for later
    comparison between cases.

To process a different case (different Mach, dynamic pressure, AoA, ...),
edit only the CONFIG block at the top.
"""

import os

import numpy as np
import matplotlib.pyplot as plt

# pv_utils — pure-numpy helpers (no ParaView dependency)
from pv_utils import (
    load_probed_coords,
    load_probed_primary_vars,
    load_probed_var,  # noqa: F401  -- kept for convenience when extending this script
    compute_pstat,
    compute_pressure_force,
    compute_lift_coefficient,
    compute_root_bending_moment,
    normalise_bending_moment,
    plot_time_series_at_point,
    plot_series,
    plot_var_vs_distance,
)
# pv_utils — ParaView-dependent (must run under pvpython)
from pv_utils.probe_xdmf import extract_cell_props


# =============================================================================
# CONFIG — edit per case
# =============================================================================
RUN_DIR        = '.'                 # working directory containing probe_out.xdmf
POST_DIR       = './post-processing' # where the .npy probe files live (and outputs go)
XDMF_FILE      = os.path.join(RUN_DIR, 'probe_out.xdmf')

PROBE_WING     = 'wing_surface_pstat'  # surface probe used for forces
PROBE_Y        = 'y_cut1'              # sample probe for pressure time-series
TARGET_STATION = (31.24, 10.88, 4.62)  # (x, y, z) of point of interest

# Gust-decay sampling on the y=const cut probe.
# A and B bracket the streamwise path the gust travels: A at the gust
# source plane, B at the wing leading edge (both at the cut's y value).
GUST_SOURCE_XYZ = (0.00, 10.88, 4.62)
WING_LE_XYZ     = (28.50, 10.88, 4.62)
LINE_TOL        = 0.5     # max perpendicular distance (m) to keep a node
DECAY_SNAPSHOTS = (0, 25, 50, 75, 100)   # timestep indices to overlay

# Flow conditions / wing reference geometry
Q       = 5500.0    # dynamic pressure  [Pa]
S       = 191.84    # reference area    [m^2]
C_MEAN  = 7.0       # reference chord   [m]

# Output filenames — encode the case so multiple cases can coexist
CASE_TAG    = 'm0650_q5500_aoa4'
CL_OUTFILE  = os.path.join(POST_DIR, f'C_L_{CASE_TAG}.npy')
BM_OUTFILE  = os.path.join(POST_DIR, f'rootBM_{CASE_TAG}.npy')


# =============================================================================
# 1. Cell properties from probe_out.xdmf  (ParaView)
# =============================================================================
print('Extracting cell Normals and Area from probe_out.xdmf ...')
pv_data = extract_cell_props(XDMF_FILE, probe_name=PROBE_WING)
normals = pv_data['Normals']
area    = pv_data['Area']
print(f'  Normals: {normals.shape}   Area: {area.shape}')


# =============================================================================
# 2. Probed primary variables + coords on the wing surface
# =============================================================================
x, y, z = load_probed_coords(POST_DIR, PROBE_WING)
prim    = load_probed_primary_vars(POST_DIR, PROBE_WING)
nt, nn  = x.shape
print(f'Wing probe: nt={nt}, nn={nn}')


# =============================================================================
# 3. Pressure, lift, root bending moment
# =============================================================================
pstat = compute_pstat(prim['ro'], prim['rovx'], prim['rovy'], prim['rovz'], prim['roe'])
F     = compute_pressure_force(pstat, area, normals)   # (nt, nn, 3)

C_L     = compute_lift_coefficient(F, q=Q, S=S)
BM      = compute_root_bending_moment(F, y)             # (nt, 3)
BM_mag  = np.linalg.norm(BM, axis=1)
BM_norm = normalise_bending_moment(BM_mag, q=Q, S=S, c_mean=C_MEAN)

os.makedirs(POST_DIR, exist_ok=True)
np.save(CL_OUTFILE, C_L)
np.save(BM_OUTFILE, BM_norm)
print(f'Saved {CL_OUTFILE} and {BM_OUTFILE}')


# =============================================================================
# 4. Diagnostic plots
# =============================================================================
plot_series(C_L,    ylabel='$C_L$',                  title='Total lift coefficient',     label='C_L',           show=False)
plot_series(BM_norm,ylabel='Normalised root BM',     title='Root bending moment',        label='root BM (norm)',show=False)

# Pressure time-series at the target station (from the y-cut probe)
x2, y2, z2 = load_probed_coords(POST_DIR, PROBE_Y)
prim_y     = load_probed_primary_vars(POST_DIR, PROBE_Y)
pstat_y    = compute_pstat(prim_y['ro'], prim_y['rovx'], prim_y['rovy'], prim_y['rovz'], prim_y['roe'])

plot_time_series_at_point(
    var=pstat_y, var_name='pstat',
    x=x2, y=y2, z=z2,
    target_coords=TARGET_STATION,
    normalisation=Q,        # plot (pstat - pstat[0]) / q
    show=False,
)


# =============================================================================
# 5. Spatial decay of rovz between gust source and wing LE (y=const cut)
# =============================================================================
# Sample rovz along the line from the gust-source plane to the wing
# leading edge at several timesteps to see how the gust signature
# attenuates as it convects toward the wing.
rovz_y = prim_y['rovz']
plot_var_vs_distance(
    var=rovz_y, var_name='rovz',
    x=x2, y=y2, z=z2,
    start=GUST_SOURCE_XYZ, end=WING_LE_XYZ,
    time_indices=DECAY_SNAPSHOTS,
    tol=LINE_TOL,
    relative_to_initial=True,   # show perturbation from the steady state
    show=False,
)

plt.show()
