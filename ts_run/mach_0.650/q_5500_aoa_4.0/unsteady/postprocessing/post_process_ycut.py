"""
post_process_ycut.py

Post-processing script for y=constant plane-cut probe data (probe_y_cut1).

Run this from the unsteady run directory with::

    python postprocessing/post_process_ycut.py

Prerequisites:
    1. python ./postprocessing/extract_probes_ycut.py
       (extracts probe_y_cut1 .npy files from probe_out.hdf5)

What it does
------------
1. Loads probe_y_cut1 data (ro, rovx, rovz, roe, pstat, x, y, z) from .npy files
2. Computes Vz = rovz / ro (vertical velocity)
3. Plots Vz decay along a line from gust source to wing LE at selected snapshots
4. Computes Cp = (pstat - pstat[t=0]) / q (pressure coefficient perturbation)
5. Plots Cp time series at a target station on the wing surface

No ParaView dependency -- runs with plain Python.
"""

import os
import numpy as np
import matplotlib.pyplot as plt

from ts_utils.pv_utils import (
    load_probed_coords,
    load_probed_var,
    find_nearest_node,
    plot_var_vs_distance,
)

# Gust gradient label and intensity
GUST_CONFIG = './gust_config.ofp'
# =============================================================================
# Read gust config: H, w_ref, Fg
# =============================================================================
gust_vars = {}
with open(GUST_CONFIG) as f:
    for line in f:
        if '=' in line:
            key, val = line.split('=', 1)
            gust_vars[key.strip()] = float(val.strip())

H_gust = int(gust_vars['H'])
w_ref  = gust_vars['w_ref']
Fg     = gust_vars['Fg']

# Gust intensity (same formula as body_force_setup.py)
w0     = (w_ref * Fg * (H_gust / 350.0) ** (1.0 / 6.0)) * 0.3048
vz_amp = w0 / 2.0   # gust velocity amplitude
print(f'Gust: H={H_gust} ft, w0={w0:.4f} m/s, vz_amp={vz_amp:.4f} m/s')

GUST_LABEL = f'H = {H_gust} ft'


# =============================================================================
# CONFIG
# =============================================================================
POST_DIR = './post-processing'
PROBE_NAME = 'probe_y_cut1'

# Flow conditions
Q = 5500.0   # dynamic pressure [Pa]

# Gust source location (x, y, z) -- from gust_config.ofp x_location
GUST_SOURCE_XYZ = (-18.42, 6.791, -0.6665)

# Target stations for Cp time series — add as many (name, (x, y, z)) as needed
CP_STATIONS = [
    ('upper surface', (8.2108, 7, 0.4351123)),
    ('lower surface', (8.2764, 7, -0.902836)),  # example — edit coords
]

# Target station for Vz decay line endpoint (typically wing LE)
WING_LE_XYZ = (5.6003, 7, -0.233582)

# Perpendicular tolerance for sampling nodes along the line [m]
LINE_TOL = 0.5

# Timestep indices to plot for Vz decay snapshots
DECAY_SNAPSHOTS = (60, 300, 400, 500, 600, 700)

# Case tag for filenames
CASE_TAG = f'm0650_q5500_aoa4_H{H_gust}'


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
# 1. Load probe data
# =============================================================================
print(f'Loading {PROBE_NAME} data from {POST_DIR}')

x, y, z = load_probed_coords(POST_DIR, PROBE_NAME)
data = load_probed_var(POST_DIR, PROBE_NAME, ['ro', 'rovx', 'rovz', 'roe', 'pstat'])
ro    = data['ro']
rovx  = data['rovx']
rovz  = data['rovz']
roe = data['roe']
pstat = data['pstat']

nt, nn = ro.shape
print(f'  nt={nt}, nn={nn}')

# =============================================================================
# 2. Compute derived quantities
# =============================================================================
# Vertical velocity
Vz = rovz / ro   # (nt, nn)

# Pressure coefficient perturbation relative to initial state
Cp = (pstat - pstat[0:1, :]) / Q   # (nt, nn)

print(f'  Vz range: [{Vz.min():.4f}, {Vz.max():.4f}]')
print(f'  Cp range: [{Cp.min():.6f}, {Cp.max():.6f}]')

# =============================================================================
# 3. Vz decay along line from gust source to wing LE
# =============================================================================
print(f'\nPlotting Vz decay from gust source to wing LE ...')
print(f'  start = {GUST_SOURCE_XYZ}')
print(f'  end   = {WING_LE_XYZ}')
print(f'  tol   = {LINE_TOL} m')
print(f'  snapshots = {DECAY_SNAPSHOTS}')

fig, ax = plt.subplots(figsize=(12, 6))
plot_var_vs_distance(
    var=Vz,
    var_name=r'$V_z$',
    x=x, y=y, z=z,
    start=GUST_SOURCE_XYZ,
    end=WING_LE_XYZ,
    time_indices=DECAY_SNAPSHOTS,
    tol=LINE_TOL,
    within_segment=True,
    relative_to_initial=True,
    normalisation=vz_amp,
    ax=ax,
    show=False,
)
ax.set_ylabel(r'$\Delta V_z \,/\, v_{z,\mathrm{amp}}$')
ax.set_title(f'Gust $V_z$ decay along line ({GUST_LABEL})')
fig.savefig(os.path.join(POST_DIR, f'Vz_decay_{CASE_TAG}.png'),
            dpi=150, bbox_inches='tight')
print(f'Saved Vz_decay_{CASE_TAG}.png')

# =============================================================================
# 4. Cp time series at target stations (one plot per station)
# =============================================================================
print(f'\nPlotting Cp time series at {len(CP_STATIONS)} station(s) ...')

cp_station_indices = []
for station_name, station_xyz in CP_STATIONS:
    idx = find_nearest_node(x, y, z, station_xyz)
    if x.ndim == 2:
        actual = (x[0, idx], y[0, idx], z[0, idx])
    else:
        actual = (x[idx], y[idx], z[idx])
    print(f'  {station_name}: target={station_xyz}, '
          f'nearest node {idx}: ({actual[0]:.4f}, {actual[1]:.4f}, {actual[2]:.4f})')
    cp_station_indices.append((station_name, idx, actual))

    Cp_at_station = Cp[:, idx]
    fig_cp, ax_cp = plt.subplots(figsize=(12, 6))
    ax_cp.plot(Cp_at_station, label=GUST_LABEL)
    ax_cp.set_xlabel('Outer timestep')
    ax_cp.set_ylabel(r'$\Delta C_p = (p - p_0) / q$')
    ax_cp.set_title(f'$\\Delta C_p$ at {station_name} (y-cut)')
    ax_cp.legend()
    ax_cp.grid(True)

    safe_name = station_name.replace(' ', '_')
    fname = f'Cp_ycut_{safe_name}_{CASE_TAG}.png'
    fig_cp.savefig(os.path.join(POST_DIR, fname), dpi=150, bbox_inches='tight')
    print(f'  Saved {fname}')

# =============================================================================
# 5. Vz time series at gust source and wing LE
# =============================================================================
print(f'\nPlotting Vz time series at gust source and wing LE ...')

idx_source = find_nearest_node(x, y, z, GUST_SOURCE_XYZ)
if x.ndim == 2:
    src_actual = (x[0, idx_source], y[0, idx_source], z[0, idx_source])
else:
    src_actual = (x[idx_source], y[idx_source], z[idx_source])

# Use first Cp station as the wing LE reference for Vz comparison
_, idx_wing_le, wing_le_actual = cp_station_indices[0]

dVz_source = (Vz[:, idx_source] - Vz[0, idx_source]) / vz_amp
dVz_wing   = (Vz[:, idx_wing_le] - Vz[0, idx_wing_le]) / vz_amp

fig3, ax3 = plt.subplots(figsize=(12, 6))
ax3.plot(dVz_source, label=f'Gust source ({src_actual[0]:.1f}, {src_actual[1]:.1f}, {src_actual[2]:.1f})')
ax3.plot(dVz_wing,   label=f'Wing LE ({wing_le_actual[0]:.1f}, {wing_le_actual[1]:.1f}, {wing_le_actual[2]:.1f})')
ax3.set_xlabel('Outer timestep')
ax3.set_ylabel(r'$\Delta V_z \,/\, v_{z,\mathrm{amp}}$')
ax3.set_title(f'Gust vertical velocity perturbation ({GUST_LABEL})')
ax3.legend()
ax3.grid(True)
fig3.savefig(os.path.join(POST_DIR, f'Vz_timeseries_{CASE_TAG}.png'),
             dpi=150, bbox_inches='tight')
print(f'Saved Vz_timeseries_{CASE_TAG}.png')

print('\nDone.')
