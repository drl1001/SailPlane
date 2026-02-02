
def body_force_function(arrays_in, arrays_out):
    import numpy as np
    import secondary_functions
    
    # =============================
    # References:
    # [1] Bartels, R. E. Development, verification and use of gust modeling in the nasa
    # computational fluid dynamics code fun3d. Tech. rep., NASA Langley Research Center,
    # 2012.
    # [2] Kenway, Gaetan & Kennedy, Graeme & Martins, Joaquim. (2014). Aerostructural 
    # optimization of the Common Research Model configuration. AIAA AVIATION 2014 -15th 
    # AIAA/ISSMO Multidisciplinary Analysis and Optimization Conference. 10.2514/6.2014-3274. 

    # =============================
    # Prescribe velocity profile (z-direction) at nodes a bit before plane
    # to model 1-cosine discrete gust. Theory based on Field Velocity Method
    # in CFD from [1].
    # Gust parameters in gust_config.ofp based on [2], which is in turn based on FAA 25.341
    # =============================

    # =============================
    # Input values:
    # =============================

    # define thin strip of gust in x-direction
    x_location = -50 # gust source about 24m away from LE of SailPlane
    d = 3 # width parameter based on mesh spacing

    # ============================
    # read config_3.ofp parameters
    # ============================
    unsteady_config = 'config_3.ofp'
    config3_cvars = secondary_functions.read_cvars(unsteady_config)

    frequency = config3_cvars['frequency']
    nstep_cycle = config3_cvars['nstep_cycle']
    ncycle = config3_cvars['ncycle']


    # with open(unsteady_config, 'r') as f:
    #     for line in f:
    #         line = line.strip()
    #         if line.startswith('frequency'):

    #             # for config file parameters which have = signs
    #             if '=' in line:
    #                 value = line.split('=')[1]
    #                 try: 
    #                     if '.' in value or 'e' in value.lower():
    #                         frequency = float(value) # for floats
    #                     else:
    #                         frequency = int(value)
    #                 except ValueError:
    #                     frequency = value
            
    #         elif line.startswith('nstep_cycle'):
    #             # for config file parameters which have = signs
    #             if '=' in line:
    #                 value = line.split('=')[1]
    #                 try: 
    #                     if '.' in value or 'e' in value.lower():
    #                         nstep_cycle = float(value) # for floats
    #                     else:
    #                         nstep_cycle = int(value)
    #                 except ValueError:
    #                     nstep_cycle = value

    #         elif line.startswith('ncycle'):
    #                 # for config file parameters which have = signs
    #                 if '=' in line:
    #                     value = line.split('=')[1]
    #                     try: 
    #                         if '.' in value or 'e' in value.lower():
    #                             ncycle = float(value) # for floats
    #                         else:
    #                             ncycle = int(value)
    #                     except ValueError:
    #                         ncycle = value

    #================================================
    # Read in aircraft velocity from initial_flow.dat
    #================================================
    f = open("../initial_flow.dat", "r")
    lines = f.readlines()
    f.close()
    V_aircraft = float(lines[2].split()[-1]) # velocity of aircraft

    #==============================================
    # Read in gust parameters from gust_config.ofp
    #==============================================
    # according to FAA-25, a sufficient number of gust gradients in the range 
    # 30 ft (9.144 m) to 350 ft (106.68 m) must be investigated
    gust_config = "gust_config.ofp"
    gust_config_cvars = secondary_functions.read_cvars(gust_config)
    H = gust_config_cvars['H'] # gust gradient in FEET!!!!!!!!
    frequency_gust = V_aircraft / (2*H*0.3048) # gust frequency in Hz, with H converted into metres
    w_ref = gust_config_cvars['w_ref'] # reference gust velocity, in FEET/SEC !!!
    Fg = gust_config_cvars['Fg'] # gust alleviation factor
    # compute gust design velocity at given H, w_ref, and Fg
    w0 = (w_ref * Fg * (H / 350)**(1/6.0)) * 0.3048 # converted to METRES/SECOND !!!
    vz_amp = w0/2
    istart = 85 # start body force at outer step 85

    # log file
    fn_log = "log_3.txt"

    # =============================
    # Get the current time step from the log file
    # =============================
    prefix = "OUTER STEP NO."
    last = None
    with open(fn_log, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith(prefix):
                
                # take whatever comes after the prefix as the number
                tail = line[len(prefix):].strip()
                
                # guard in case the line is incomplete
                if tail and tail.split()[0].isdigit():
                    istep_now = int(tail.split()[0])
                    
    print("Current outer step is %i" % (istep_now, ))

    # =============================
    # ADDED: Write to log_bf.txt to verify function is being called
    # Test whether unsteady simulation is calling the body_force_function or not
    # =============================
    # with open("log_bf.txt", "a") as log_file:
    #    log_file.write(f"time step: {istep_now}, modelling gust\n")

    # =============================
    # Data from arrays_in
    # can access this from solver
    # =============================
    
    x = arrays_in["x"]
    y = arrays_in['y']
    z = arrays_in['z']
    ro = arrays_in["ro"]
    vol = arrays_in["vol"]

    # =============================
    # Get indices of the nodes within distance d of x_location
    # i.e. find node indices within the width d of the thin strip
    # =============================

    idx = np.where(np.abs(x - x_location) <= d)[0]

    # write coords of the selected nodes in the thin strip into a .csv for checking in paraview
    # Combine arrays into 2D array and save
    data_to_save = np.column_stack([x[idx], y[idx], z[idx]])
    np.savetxt('../thin_strip_coord.csv', data_to_save, delimiter=',', header='x,y,z', comments='')

    # =============================
    # Generate the input vy for all time steps
    # =============================
    nstep = nstep_cycle * ncycle # total number of outer steps
    steps = np.arange(nstep)
    # tru_step is the physical time length for each outer step
    tru_step = 1.0 / (frequency * float(nstep_cycle))

    # time since start
    tau = (steps - istart) * tru_step # time since start of gust
    duration = 1.0 / (2.0 * frequency_gust) # gust half-cycle time length
    vz = np.zeros_like(tau, dtype=float) # initialise array to store gust velocity with same shape as tau
    mask = (tau >= 0.0) & (tau <= duration) # include the end point (returns to 0) -> only use half cycle of gust
    vz[mask] = vz_amp * (1 - np.cos(2.0 * np.pi * frequency_gust * tau[mask])) # defines 1-cosine gust


    # ==================
    # Set body force
    # ==================
    # Get the fz array from arrays_out

    # set the fz at the required location using the input vy for this step

    # Also, WHY divide by volume (like in the examples file)?????
    arrays_out['fbody_z'][idx] = ro[idx]*vz[istep_now]
    # /(vol[idx] * tru_step)
