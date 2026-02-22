'''
For setting up parameters needed for body_force_function.
Such as gust parameters and step counter.
Every outer step, the pickle file is read to get the gust parameters and
other relevant data, and increments the step counter by 1.
'''
import pickle
import numpy as np

def read_cvars(fname):
    '''
    Read config ofp file that have format variable_name = ...
    Stores these in dictionary cvars.
    '''
    global_vars = {}
    local_vars = {}
    f = open(fname, "r")
    s = f.read()
    exec(s, global_vars, local_vars)
    f.close()

    cvars = {}
    for var in local_vars:
        cvars[var] = local_vars[var]

    return cvars

# ========================
# Load input configs
# ========================
config3 = read_cvars("config_3.ofp")
frequency = config3["frequency"]
nstep_cycle = config3["nstep_cycle"]
ncycle = config3["ncycle"]
nstep_inner = config3['nstep'] # a bit confusing to name nstep as total no. of steps later on. 
#But nstep in config_3 is no. of inner steps per outer step

with open("../initial_flow.dat", "r") as f:
    lines = f.readlines()
V_aircraft = float(lines[2].split()[-1])

gust_config = read_cvars("gust_config.ofp")
H = gust_config["H"]
w_ref = gust_config["w_ref"]
Fg = gust_config["Fg"]
x_location = gust_config['x_location']
d = gust_config['d']

# convert H from to meters
H_m = H * 0.3048
w0 = (w_ref * Fg * (H / 350.0) ** (1/6.0)) * 0.3048
vz_amp = w0 / 2.0
frequency_gust = V_aircraft / (2 * H_m)

tru_step = 1.0 / (frequency * float(nstep_cycle))
nstep_outer = nstep_cycle * ncycle # total no. of outer steps
istart = 85

# Precompute gust profile for all steps
steps = np.arange(nstep_outer)
tau = (steps - istart) * tru_step
duration = 1.0 / (2.0 * frequency_gust)
vz = np.zeros_like(tau)
mask = (tau >= 0.0) & (tau <= duration)
vz[mask] = vz_amp * (1.0 - np.cos(2.0 * np.pi * frequency_gust * tau[mask]))

# Save all data in a dictionary
body_force_data = {
    "istep_now": 0,
    'inner_step': 0,
    'nstep_inner' : nstep_inner, # no. of inner steps per outer step
    "nstep_outer": nstep_outer, # total number of outer steps
    "tru_step": tru_step,
    "istart": istart,
    "vz": vz,
    "x_location": x_location,
    "d": d,
    "initialized": False  # optional flag
}

# Write pickle
with open("body_force_data.pkl", "wb") as f:
    pickle.dump(body_force_data, f)

print("body_force_data.pkl initialized, can run unsteady with body_force_function now.")
