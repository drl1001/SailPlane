"""
extract_normals_area.py

Extract surface Normals and Area from probe_out.xdmf using a single
ParaView pipeline that selects all wing probe blocks at once.

Run with pvpython (from the unsteady run directory):
    pvpython ./postprocessing/extract_normals_area.py

This must be run ONCE before post_process.py. Outputs are loaded
directly by post_process.py without needing pvpython.

Pipeline:
    XDMFReader
        -> ExtractBlock (all wing probes at once)
        -> ExtractSurface
        -> SurfaceNormals
        -> CellSize
        -> CellDatatoPointData  (Area, Normals)

Output:
    ./post-processing/normals.npy    (nn, 3)  — surface normals
    ./post-processing/area.npy       (nn,)    — cell area at each point
"""

import os
import sys

import paraview
paraview.compatibility.major = 5
paraview.compatibility.minor = 13

from paraview.simple import (
    XDMFReader,
    ExtractBlock,
    ExtractSurface,
    SurfaceNormals,
    CellSize,
    CellDatatoPointData,
    UpdatePipeline,
)
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
PROBE_SELECTORS = [
    '/Root/probe_le',
    '/Root/probe_wing_middle',
    '/Root/probe_main_wing',
    '/Root/probe_root_wing',
    '/Root/probe_te',
    '/Root/probe_tip',
]

# =============================================================================
# PIPELINE
# =============================================================================
paraview.simple._DisableFirstRenderCameraReset()

# 1. Read XDMF
reader = XDMFReader(
    registrationName='probe_out.xdmf',
    FileNames=[XDMF_FILE],
)
UpdatePipeline()

# 2. Extract all wing probe blocks at once
extractBlock = ExtractBlock(
    registrationName='ExtractBlock_wing',
    Input=reader,
)
extractBlock.Selectors = PROBE_SELECTORS
UpdatePipeline()

# 3. Extract surface
extractSurface = ExtractSurface(
    registrationName='ExtractSurface_wing',
    Input=extractBlock,
)
UpdatePipeline()

# 4. Surface normals
surfaceNormals = SurfaceNormals(
    registrationName='SurfaceNormals_wing',
    Input=extractSurface,
)
surfaceNormals.ComputeCellNormals = 1
UpdatePipeline()

# 5. Cell size (Area only)
cellSize = CellSize(
    registrationName='CellSize_wing',
    Input=surfaceNormals,
)
cellSize.ComputeVertexCount = 0
cellSize.ComputeLength = 0
cellSize.ComputeVolume = 0
UpdatePipeline()

# 6. Cell data to point data
cellToPoint = CellDatatoPointData(
    registrationName='CellDatatoPointData_wing',
    Input=cellSize,
)
cellToPoint.CellDataArraytoprocess = ['Area', 'Normals']
UpdatePipeline()

# =============================================================================
# EXTRACT
# =============================================================================
print('\nExtracting Normals and Area ...')
pv_data = PVDataToNumpy(cellToPoint)

normals = pv_data['Normals']
area    = pv_data['Area']

print(f'  Normals: {normals.shape}')
print(f'  Area:    {area.shape}')

# =============================================================================
# SAVE
# =============================================================================
os.makedirs(POST_DIR, exist_ok=True)

np.save(os.path.join(POST_DIR, 'normals.npy'), normals)
np.save(os.path.join(POST_DIR, 'area.npy'), area)

print(f'\nSaved to {POST_DIR}:')
print(f'  normals.npy   {normals.shape}')
print(f'  area.npy      {area.shape}')
