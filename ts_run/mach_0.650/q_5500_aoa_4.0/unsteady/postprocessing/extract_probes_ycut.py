"""
Extract y=constant plane-cut probe data from probe_out.hdf5 as .npy files.

Wing surface probes are now extracted via extract_normals_area.py (pvpython).
This script only extracts the y=constant plane-cut probes from HDF5.

Run this BEFORE post_process_ycut.py:
    python ./postprocessing/extract_probes_ycut.py
"""

from ts_utils.pv_utils import extract_probes

HDF5_FILE = './probe_out.hdf5'
POST_DIR  = './post-processing/probe_y_cut1'

# Plane-cut probes only (wing surface probes handled by extract_normals_area.py)
PROBES_YCUT = ['probe_y_cut1']
VARS_YCUT   = ['ro', 'rovx', 'rovy', 'rovz', 'roe', 'x', 'y', 'z', 'pstat']

extract_probes(
    hdf5_file=HDF5_FILE,
    out_dir=POST_DIR,
    probes=PROBES_YCUT,
    variables=VARS_YCUT,
)
