"""
Extract probe data from probe_out.hdf5 and save as .npy files.

Run this BEFORE post_process.py:
    python ./postprocessing/extract_probes.py
"""

from ts_utils.pv_utils import extract_probes

HDF5_FILE = './probe_out.hdf5'
POST_DIR  = './post-processing'

# Surface probes (wing patches)
PROBES_SURFACE = [
    'probe_le',
    'probe_wing_middle',
    'probe_main_wing',
    'probe_root_wing',
    'probe_te',
    'probe_tip',
]
VARS_SURFACE = ['ro', 'rovx', 'rovy', 'rovz', 'roe', 'x', 'y', 'z', 'twall_x', 'pstat']

# Plane-cut probes
PROBES_YCUT = ['probe_y_cut1']
VARS_YCUT   = ['ro', 'rovx', 'rovy', 'rovz', 'roe', 'x', 'y', 'z', 'pstat']

# Build per-probe variable mapping
probe_vars = {p: VARS_SURFACE for p in PROBES_SURFACE}
probe_vars.update({p: VARS_YCUT for p in PROBES_YCUT})

ALL_PROBES = PROBES_SURFACE + PROBES_YCUT

extract_probes(
    hdf5_file=HDF5_FILE,
    out_dir=POST_DIR,
    probes=ALL_PROBES,
    probe_vars=probe_vars,
)
