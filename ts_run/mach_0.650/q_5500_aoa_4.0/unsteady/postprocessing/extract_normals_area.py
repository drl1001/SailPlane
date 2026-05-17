"""
extract_normals_area.py

Extract all probed variables, surface Normals, Area, and pressure force
from probe_out.xdmf using a single ParaView pipeline at ALL timesteps.

All wing probe blocks are selected at once, ensuring consistent point
ordering between Normals/Area and the flow variables.

Run with pvpython (from the unsteady run directory):
    pvpython ./postprocessing/extract_normals_area.py

Output (all saved to ./post-processing/):
    normals.npy    (nn, 3)      — surface normals (static)
    area.npy       (nn,)        — cell area (static)
    p_force.npy    (nt, nn, 3)  — pressure force vector
    pstat.npy      (nt, nn)     — static pressure
    ro.npy         (nt, nn)     — density
    rovx.npy       (nt, nn)     — x-momentum
    rovy.npy       (nt, nn)     — y-momentum
    rovz.npy       (nt, nn)     — z-momentum
    roe.npy        (nt, nn)     — total energy
    twall_x.npy    (nt, nn)     — wall shear stress x
    x.npy          (nt, nn)     — x coordinates
    y.npy          (nt, nn)     — y coordinates
    z.npy          (nt, nn)     — z coordinates
"""

import os
import sys

import paraview
paraview.compatibility.major = 5
paraview.compatibility.minor = 13

from paraview.simple import *
import numpy as np

# Add ts_utils to path
ts_utils_parent = "/rds/project/rds-UemeQPgBLn8/users/yl924"
if ts_utils_parent not in sys.path:
    sys.path.insert(0, ts_utils_parent)

from ts_utils.pv_utils.PVDataToNumpy import PVDataToNumpy

# =============================================================================
# CONFIG
# =============================================================================
XDMF_FILE = './probe_out.xdmf'
POST_DIR  = './post-processing'

# Block selectors for the wing surface probes in probe_out.xdmf.
# These must match the probes defined in probes.py.
PROBE_SELECTORS = [
    '/Root/probe_le',
    '/Root/probe_main_wing',
    '/Root/probe_root_wing',
    '/Root/probe_te',
    '/Root/probe_tip',
    '/Root/probe_wing_middle',
]

# Scalar variables to extract at every timestep.
# These are the PointArrays available in the XDMF reader — they come from
# Turbostream's probe output and are stored per-node at every saved timestep.
SCALAR_VARS = ['pstat', 'ro', 'rovx', 'rovy', 'rovz', 'roe', 'twall_x', 'x', 'y', 'z']

# =============================================================================
# PIPELINE CONSTRUCTION
# =============================================================================
# The pipeline processes all wing probes together so that every array
# extracted via PVDataToNumpy shares the same point ordering.
#
# Pipeline stages:
#   XDMFReader          — reads probe_out.xdmf (all timesteps, all probes)
#   ExtractBlock        — selects only the wing surface probe blocks
#   ExtractSurface      — converts volume cells to surface polygons
#   SurfaceNormals      — computes outward-facing normals per cell/point
#   CellSize            — computes cell Area (as cell data)
#   CellDatatoPointData — interpolates Area from cells to points
#   Calculator          — computes p_force = pstat * Normals * Area per point
#
# At the end of this pipeline, each point has:
#   - All original probed scalar arrays (pstat, ro, rovx, ..., x, y, z)
#     which vary with time (one value per point per timestep)
#   - Normals (3-component vector) — static, same at all timesteps
#   - Area (scalar) — static, same at all timesteps
#   - p_force (3-component vector) — time-varying, computed from pstat * Normals * Area

paraview.simple._DisableFirstRenderCameraReset()

# 1. Read XDMF — load all point arrays that were probed
reader = XDMFReader(
    registrationName='probe_out.xdmf',
    FileNames=[XDMF_FILE],
)
reader.PointArrayStatus = ['pstat', 'ro', 'roe', 'rovx', 'rovy', 'rovz', 'twall_x', 'x', 'y', 'z']
UpdatePipeline()

# Get all available timesteps from the reader
timesteps = reader.TimestepValues
nt = len(timesteps)
print(f'Found {nt} timesteps in {XDMF_FILE}')

# 2. Extract all wing probe blocks at once — ParaView merges them internally
extractBlock1 = ExtractBlock(registrationName='ExtractBlock1', Input=reader)
extractBlock1.Selectors = PROBE_SELECTORS
UpdatePipeline()

# 3. Extract surface — convert 3D cells to surface polygons
extractSurface1 = ExtractSurface(registrationName='ExtractSurface1', Input=extractBlock1)
UpdatePipeline()

# 4. Surface normals — compute outward normals (needed for force direction)
surfaceNormals1 = SurfaceNormals(registrationName='SurfaceNormals1', Input=extractSurface1)
surfaceNormals1.ComputeCellNormals = 1
UpdatePipeline()

# 5. Cell size — compute cell Area as cell data
cellSize1 = CellSize(registrationName='CellSize1', Input=surfaceNormals1)
cellSize1.ComputeVertexCount = 0
cellSize1.ComputeLength = 0
cellSize1.ComputeVolume = 0
UpdatePipeline()

# 6. Cell data to point data — interpolate Area from cell centres to nodes
#    so that Area has the same (nn,) shape as the other point arrays
cellDatatoPointData1 = CellDatatoPointData(registrationName='CellDatatoPointData1', Input=cellSize1)
cellDatatoPointData1.CellDataArraytoprocess = ['Area']
UpdatePipeline()

# 7. Calculator — compute pressure force vector at each point:
#    p_force = pstat * Normals * Area   (element-wise multiply)
#    pstat varies per timestep; Normals and Area are static geometry.
p_force = Calculator(registrationName='p_force', Input=cellDatatoPointData1)
p_force.ResultArrayName = 'p_force'
p_force.Function = 'pstat*Normals*Area'
UpdatePipeline()

SetActiveSource(p_force)

# =============================================================================
# EXTRACT AT FIRST TIMESTEP — determine nn and get static arrays
# =============================================================================
scene = GetAnimationScene()
scene.AnimationTime = timesteps[0]
UpdatePipeline(time=timesteps[0], proxy=p_force)

# PVDataToNumpy fetches the VTK dataset at the CURRENT timestep and returns
# all PointData and CellData arrays as numpy arrays in a dict.
# At this point it returns arrays of shape (nn,) for scalars, (nn,3) for vectors.
pv_data = PVDataToNumpy(p_force)

print('\nArrays available at first timestep:')
for key, arr in pv_data.items():
    print(f'  {key}: {arr.shape}')

# Normals and Area are static (geometry doesn't change between timesteps)
# so we only need to extract them once.
normals = pv_data['Normals']
area    = pv_data['Area']
nn = normals.shape[0]
print(f'\nnn = {nn}, nt = {nt}')

# =============================================================================
# LOOP OVER ALL TIMESTEPS — extract time-varying arrays
# =============================================================================
# PVDataToNumpy only returns data at the current animation time. To build
# (nt, nn) arrays we must advance the animation time, update the pipeline,
# and extract at each timestep.
#
# At each timestep, the probed scalars (pstat, ro, ..., x, y, z) are
# updated by the XDMF reader, and the Calculator recomputes p_force using
# the new pstat values (Normals and Area remain constant).

# Pre-allocate output arrays
p_force_all = np.zeros((nt, nn, 3))
scalars = {var: np.zeros((nt, nn)) for var in SCALAR_VARS}

print(f'\nExtracting data over {nt} timesteps ...')

for i, t in enumerate(timesteps):
    # Advance ParaView's animation to timestep t
    scene.AnimationTime = t
    # Update the pipeline so that the XDMF reader loads data at time t,
    # and downstream filters (including the Calculator) recompute.
    UpdatePipeline(time=t, proxy=p_force)

    # Fetch all point arrays at this timestep as numpy arrays
    pv_data = PVDataToNumpy(p_force)

    # Store p_force (3-component vector) for this timestep
    p_force_all[i] = pv_data['p_force']

    # Store each scalar variable for this timestep
    for var in SCALAR_VARS:
        if var in pv_data:
            scalars[var][i] = pv_data[var]

    # Print progress every 50 steps
    if (i + 1) % 50 == 0 or i == 0 or i == nt - 1:
        print(f'  step {i+1}/{nt}  t={t}')

# =============================================================================
# SAVE
# =============================================================================
os.makedirs(POST_DIR, exist_ok=True)

# Static geometry arrays (same at all timesteps)
np.save(os.path.join(POST_DIR, 'normals.npy'), normals)
np.save(os.path.join(POST_DIR, 'area.npy'), area)
print(f'\nSaved normals.npy  {normals.shape}')
print(f'Saved area.npy     {area.shape}')

# Time-varying pressure force: (nt, nn, 3)
np.save(os.path.join(POST_DIR, 'p_force.npy'), p_force_all)
print(f'Saved p_force.npy  {p_force_all.shape}')

# Time-varying scalar fields: each (nt, nn)
for var in SCALAR_VARS:
    np.save(os.path.join(POST_DIR, f'{var}.npy'), scalars[var])
    print(f'Saved {var}.npy     {scalars[var].shape}')

print(f'\nDone. All arrays saved to {POST_DIR}')
