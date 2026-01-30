'''
Body forces used to model gusts as time-dependent
source terms (instead of convecting the gust as a inlet boundary condition which
is very computationally expensive).

This script is for setting up pre-processing - setup relevant directories and copies over input_1.hdf5 into steady and unsteady directories.
Run steady 1, 2 and unsteady using slurm submission. Faster, less queue time.

Script can be run just to set up pre, steady and unsteady directories given initial
and boundary conditions. Calculates intial and boundary conditions and output to file.


'''

import numpy as np
import os



if __name__ == '__main__':

    # set pre=True to use scripted paraview to generate input_1.hdf5
    # set pre=False to only print the freestream and boundary conditions and copy the directories 
    # and generate the bcs and initial condition dat files
    pre = True

    # name of paraview scripted pre python file
    pre_name = 'generate_input_1.py'


    # Specify Mach number, velocity and dynamic pressure for each case


    cases = [
        [0.85, 231.4, 5000.,0.0],
        [0.85, 231.4, 5250.,0.0],
        [0.85, 231.4, 5500.,0.0],
        [0.85, 231.4, 5750.,0.0],
        [0.85, 231.4, 6000.,0.0],
    ]

    # Specify which cases we wish to run
    icase_st = 2
    icase_en = 3

    # Specify TS executable syntax
    ts_ver = 4310
    ts_options = "-x UCX_MEMTYPE_CACHE=n -x UCX_NET_DEVICES=mlx5_0:1,mlx5_1:1 -x UCX_TLS=rc,tcp,cuda_copy,cuda_ipc,gdr_copy"
    ts_exe = f"/usr/local/software/turbostream/ts{ts_ver}/a100_pv513/turbostream_4/bin/turbostream.py"
    ngpu = 1
    ngpu_per_node = 4
    
    # Gas constants
    ga = 1.4
    cp = 1005.

    cv = cp/ga
    rgas = cp-cv


    for icase in range(icase_st, icase_en):
        print()
        print(f"Setting up case {icase}")
        
        m = cases[icase][0]
        v = cases[icase][1]
        q = cases[icase][2]
        alpha = cases[icase][3]
        print(f"M = {m:4.3f}")
        print(f"v = {v:5.1f}")
        print(f"q = {q:5.1f}") 
        print(f'AoA alpha = {alpha:1.1f}')       

        # Get non-dimensional flow conditions from the Mach number
        q_div_p0 = 0.5*ga*m*m*np.power(1.0 + 0.5*(ga-1.0)*m*m, -1.0*ga/(ga-1.0)) # get q/p0
        p_div_p0 = np.power(1.0 + 0.5*(ga-1.0)*m*m, -1.0*ga/(ga-1.0)) # get p/p0
        t_div_t0 = np.power(1.0 + 0.5*(ga-1.0)*m*m, -1.0) # get t/t0
        v_div_sqrtcpt0 = np.sqrt(ga-1.0)*m*np.power(1.0 + 0.5*(ga-1.0)*m*m, -0.5) # get v/sqrt(cp*t0)

        # Get dimensional values
        p0 = q/q_div_p0
        t0 = np.power(v/v_div_sqrtcpt0, 2.0)/cp
        p = p0*p_div_p0
        t = t0*t_div_t0
        ro = p/(rgas*t)
        h0 = cp*t0
        print("ro = %5.4f" % (ro, ))

        print("\nFreestream boundary conditions:")
        print("Mach = %5.4f" % (m, ))
        print("Static temperature = %e" % (t, ))
        print("Static pressure = %e" % (p, ))
        print(f'Stagnation enthalpy = {h0}')
        print(f'Stagnation pressure = {p0}')
        print(F'Stagnation temperature = {t0}')
        
        
        # Check if the mach number directory exists
        dir1 = "mach_%4.3f" % (m, )
        if os.path.isdir(dir1):
            print("Directory %s already exists" % (dir1, ))
        else:
            print("Making directory %s" % (dir1, ))
            os.makedirs(dir1)

        # Check if the dynamic pressure directory exists
        dir2 = "%s/q_%i" % (dir1, q)
        if os.path.isdir(dir2):
            print("Directory %s already exists" % (dir2, ))
        else:
            print("Making directory %s" % (dir2, ))
            os.makedirs(dir2)

        # Copy the files from template to the new location
        src = "template_mach/template_point/"
        cmd = "cp -rP template_mach/template_point/* %s/." % (dir2)
        print(cmd)
        os.system(cmd)
        
        # Write boundary conditions file
        fn = "%s/bcs.dat" % (dir2)
        f = open(fn, "wt")
        f.write("Mach = %e\n" % (m, ))
        f.write("Static pressure = %e\n" % (p, ))
        f.write("Static temperature = %e\n" % (t, ))
        f.write("alpha = %e\n" % (alpha, ))
        f.close()

        # Write initial flow file
        fn = "%s/initial_flow.dat" % (dir2)
        f = open(fn, "wt")
        f.write("Stagnation enthalpy = %e\n" % (h0, ))
        f.write("Stagnation pressure = %e\n" % (p0, ))
        f.write("Vx = %e\n" % (v, ))
        f.close()
        
        
        # os.chdir(f'{dir2}')
        print(os.getcwd())
        # Run pre
        os.chdir("%s/pre" % (dir2, ))
        print(os.getcwd())
        # run scripted paraview to create topology and flow conditions 
        # -> output input_1.hdf5
        if pre:
            # run scripted pvpython code to generate input_1.hdf5
            cmd = f"pvpython {pre_name}"
            os.system(cmd)
        else:
            # manually creating input_1.hdf5 in paraview
            print('Already created input_1.hdf5 manually in paraview')
        os.chdir("../")

        # Copy contents in temporary steady to actual steady folder.
        os.chdir("steady")
        print(os.getcwd())
        # create soft link to ../pre/input_1.hdf5, but this soft link is in the directory steady.
        # cmd = "ln -s ../pre/input_1.hdf5 ." 
        # Remove existing link/file if it exists, then create new link
        cmd = "rm -f input_1.hdf5 && ln -s ../pre/input_1.hdf5 ."
        os.system(cmd)
        
        fn_config = "config_1.ofp"  # config 1 is inviscid (Euler)
        fn_topo_in = "input_1.hdf5"
        fn_geom_in = "input_1.hdf5"
        fn_flow_in = "input_1.hdf5"
        fn_flow_out = "output_1"
        fn_log = "log_1.txt"
    
        cmd = "mpirun --bind-to none -np %i %s python %s %s %s %s %s %s %i > %s 2>&1" % (ngpu, ts_options, ts_exe, fn_config, fn_topo_in, fn_geom_in, fn_flow_in, fn_flow_out, ngpu_per_node, fn_log)
        print(cmd)
        # uncomment line below to run steady 1 case directly using python (i.e. not using slurm submission script)
        # os.system(cmd)

        fn_config = "config_2.ofp" # config 2 is viscous (contains Turbulence model for boundary layers)
        fn_topo_in = "input_1.hdf5" 
        fn_geom_in = "input_1.hdf5"
        fn_flow_in = "output_1.hdf5"
        fn_flow_out = "output_2"
        fn_log = "log_2.txt"
    
        cmd = "mpirun --bind-to none -np %i %s python %s %s %s %s %s %s %i > %s 2>&1" % (ngpu, ts_options, ts_exe, fn_config, fn_topo_in, fn_geom_in, fn_flow_in, fn_flow_out, ngpu_per_node, fn_log)
        print(cmd)
        # uncomment line below to run steady 2 directly
        # os.system(cmd)
        os.chdir("../")
        

        # Set up unsteady simulation directory
        os.chdir("unsteady")
        print(os.getcwd())
        # create soft link to ../pre/input_1.hdf5, but this soft link is in the directory unsteady.
        # cmd = "ln -s ../pre/input_1.hdf5 ." 
        # Remove existing link/file if it exists, then create new link
        cmd = "rm -f input_1.hdf5 && ln -s ../pre/input_1.hdf5 ."
        os.system(cmd)