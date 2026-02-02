def custom_secondary_function(g, custom_secondary_global):
	
	#=================
	# Some notes on GPUs
	#=================
	# Host - CPU; Device - GPU
	# Device memory - the physical DRAM attached to a GPU - it's the memory accessed 
	# over the GPU external memory bus.
	# Global memory is the LOGICAL, ADDRESSABLE space within that physical memory accessible by all 
	# GPU threads and the CPU (the host).
	# Global memory is the primary, large-capacity, but slower memory area used for data transfer and storage
	# N.B. global memory is the logical address space that resides WITHIN the physical device memory (DRAM)

	# custom_secondary_global is a GPU handle cache and state container which persists ACROSS time steps
	# custom_secondary global is only initialised ONCE at the beginning of the CFD run.
	# custom_secondary_function runs EVERY TIMESTEP, and is where I interact with the entire domain

	# GPU hierarchy
	# secondary_functions have the CUDA kernels (the functions being run in parallel on the GPU)
	# smallest working unit are threads, a group of threads in a BLOCK share fast memory and can
	# synchronise with each other. 
	# All threads run the same code (i.e. same kernel) in parallel on different data, and knows its 
	# IDs (threadIdx, blockIdx etc.)
	# A GRID contains all the blocks launched for a kernel




	#=================
	# Get the number of domains and the domain id of each node
	#================
	import time
	time_st_global = time.time()
	arrays_out = {}
	
	#=================
	# On the first step, initialise the dictionary and load all data and set guess
	#=================
	if len(custom_secondary_global.keys()) == 1:
		print("\nInitialising custom secondary dictionary")
		
		# First step
		# Import all modules and save to custom_secondary_global
		# Generate all required arrays and save to custom_secondary global

		

		# Import modules and save
		import secondary_functions
		import scipy
		import numpy as np
		# from cupyx.scipy.interpolate import RegularGridInterpolator
		# import cupy as cp
		import ts.util.format as ts_format
		import secondary_functions
		import time
		import math
		from mpi4py import MPI
		from secondary_functions import ts_print
		import h5py
		from numba import cuda
		
		custom_secondary_global["numpy"] = np
		custom_secondary_global["math"] = math
		custom_secondary_global["ts_format"] = ts_format
		custom_secondary_global["ts_print"] = ts_print
		custom_secondary_global["secondary_functions"] = secondary_functions
		custom_secondary_global["time_module"] = time
		custom_secondary_global["MPI"] = MPI

		# Initialise counters and save
		custom_secondary_global["istep"] = 0
		custom_secondary_global["istep_rk"] = 0

		# store geometry of domain in global (not in arrays_in)
		# this is only done once, and treated as read-only metadata
		for aname in ["x", "y", "z", "node_id", "omega", "idomain", "procid"]:
			a = g.get_domain_array(aname)
			custom_secondary_global[aname] = a
		

		omega = custom_secondary_global["omega"]
		procid = custom_secondary_global["procid"]
		ndom = len(omega)
		custom_secondary_global["nnode"] = len(procid)
		custom_secondary_global["ndom"] = ndom
	   

		#=======================================================================
		# Modify this section for my own use
		# I don't need these, the multispecies_config are for Ellis.

		## get scheme details and save
		## read variables in custom config ofp and store them in dictionary cvars 

		# cvars = secondary_functions.read_cvars("multispecies_config.ofp")
		# custom_secondary_global["cvars"] = cvars

		# with h5py.File('ice_growth_fits.hdf5', 'r') as f:
		# 	# Load arrays from file
		# 	a = np.array(f['a'])
		# 	b = np.array(f['b'])
		# 	m0 = np.array(f['m0'])
		# 	gamma = np.array(f['gamma'])
		# 	delta = np.array(f['delta'])
		# 	p = np.array(f['p'])
		# 	T = np.array(f['T'])

		# # Transfer arrays to GPU - allocates GPU memory, copies from CPU to GPU once at the start
		# # after this transfer, kernels read these from GPU directly, no more PCle traffic.
		# a_d = cuda.to_device(a)
		# b_d = cuda.to_device(b)
		# m0_d = cuda.to_device(m0)
		# gamma_d = cuda.to_device(gamma)
		# delta_d = cuda.to_device(delta)
		# p_d = cuda.to_device(p)
		# T_d = cuda.to_device(T)

		# # Store device pointers in custom_secondary_global. These are stored in GPU memory for fast access
		# custom_secondary_global['fit_a_d'] = a_d
		# custom_secondary_global['fit_b_d'] = b_d
		# custom_secondary_global['fit_m0_d'] = m0_d
		# custom_secondary_global['fit_gamma_d'] = gamma_d
		# custom_secondary_global['fit_delta_d'] = delta_d
		# custom_secondary_global['fit_p_d'] = p_d
		# custom_secondary_global['fit_T_d'] = T_d

		# End of modified section for myself
		#==========================================================================

	#=================
	# Start of code carried out at every step
	#================
	
    # Retrieves pointers to all python libraries from custom_secondary_global to be used locally
	# each time step
	time_module = custom_secondary_global["time_module"]
	time_st = time_module.time()
	numpy = custom_secondary_global["numpy"]
	ts_format = custom_secondary_global["ts_format"]
	ts_print = custom_secondary_global["ts_print"]
	secondary_functions = custom_secondary_global["secondary_functions"]
	istep = custom_secondary_global["istep"]
	istep_rk = custom_secondary_global["istep_rk"]
	secondary_functions = custom_secondary_global["secondary_functions"]
	nnode = custom_secondary_global["nnode"]
	ndom = custom_secondary_global["ndom"]
   
	MPI = custom_secondary_global["MPI"]
   

	mpi_comm = MPI.COMM_WORLD
	mpi_rank = mpi_comm.Get_rank()
	#ts_print("Step number = %i, rk step number = %i" % (istep, istep_rk))

	   
	#=================
	# Begin loop over all domains for setting secondary variables
	#================ 
	time_st = time_module.time()


	# get the domain array pointers
	# note that these point directly to device memory (in DRAM), i.e. these are only POINTERS 
	# to the GPU memory. Gather coords and primary variables pointers
	x_d = g.get_domain_array_ptr("x")
	y_d = g.get_domain_array_ptr("y")
	z_d = g.get_domain_array_ptr("z")
	ro_d = g.get_domain_array_ptr("ro")
	rovx_d = g.get_domain_array_ptr("rovx")
	rovy_d = g.get_domain_array_ptr("rovy")
	rovz_d = g.get_domain_array_ptr("rovz")
	roe_d = g.get_domain_array_ptr("roe")
	#====================
	# don't need any scalars or scalar sources for me
	# scalar0_d = g.get_domain_array_ptr("scalar0")
	# scalar1_d = g.get_domain_array_ptr("scalar1")
	# scalar2_d = g.get_domain_array_ptr("scalar2")
	# scalarnd0_d = g.get_domain_array_ptr("scalarnd0")
	# scalarnd1_d = g.get_domain_array_ptr("scalarnd1")
	# scalarnd2_d = g.get_domain_array_ptr("scalarnd2")
	# ro_src_d = g.get_domain_array_ptr("ro_source")
	# rovx_src_d = g.get_domain_array_ptr("rovx_source")
	# rovy_src_d = g.get_domain_array_ptr("rovy_source")
	# rovz_src_d = g.get_domain_array_ptr("rovz_source")
	# roe_src_d = g.get_domain_array_ptr("roe_source")
	# scalar0_src_d = g.get_domain_array_ptr("scalar0_source")
	# scalar1_src_d = g.get_domain_array_ptr("scalar1_source")
	# scalar2_src_d = g.get_domain_array_ptr("scalar2_source")
	#======================

	# Gather secondary variables pointers already computed in solver from GPU
	vol = g.get_domain_array_ptr("vol")
	time_step = g.get_domain_array_ptr("time_step") # inner
	idomain_d = g.get_domain_array_ptr("idomain")
	omega_d = g.get_domain_array_ptr("omega")
	
	vx_d = g.get_domain_array_ptr("vx")
	vy_d = g.get_domain_array_ptr("vy")
	vz_d = g.get_domain_array_ptr("vz")
	vrotx_d = g.get_domain_array_ptr("vrotx")
	vroty_d = g.get_domain_array_ptr("vroty")
	vrotz_d = g.get_domain_array_ptr("vrotz")
	tstat_d = g.get_domain_array_ptr("tstat")
	pstat_d = g.get_domain_array_ptr("pstat")
	pstag_d = g.get_domain_array_ptr("pstag")
	hstag_d = g.get_domain_array_ptr("hstag")
	tstag_d = g.get_domain_array_ptr("tstag")
	viscosity_laminar_d = g.get_domain_array_ptr("viscosity_laminar")
	asound_d = g.get_domain_array_ptr("asound")
	

	# TODO: need to change the functions in secondary_functions, which are the kernels run on GPU
	# Python only launches the kernels, no actual maths happens in python

	# I don't think I need this as I'm just extracting pstat from the domain, not actually changing it.
	# secondary_functions.set_secondary(nnode, ndom, x_d, y_d, z_d,time_step,vol,
	# 								  ro_d, rovx_d, rovy_d, rovz_d, roe_d,
	# 								  scalar0_d, scalar1_d, scalar2_d,
	# 								  scalarnd0_d, scalarnd1_d, scalarnd2_d,
	# 								  ro_src_d, rovx_src_d, rovy_src_d, rovz_src_d, roe_src_d,
	# 								  scalar0_src_d, scalar1_src_d, scalar2_src_d,
	# 								  idomain_d, omega_d,
	# 								  vx_d, vy_d, vz_d, vrotx_d, vroty_d, vrotz_d,
	# 								  tstat_d, pstat_d, pstag_d, hstag_d, tstag_d,
	# 								  viscosity_laminar_d, asound_d,
	# 								  custom_secondary_global)

	# extract pstat from device (GPU) to host (CPU)
	

	# ensures all ranks finish GPU kernels, source terms are consistent, no race between partitions
	mpi_comm.Barrier()
	time_en = time_module.time()
	
	

def custom_bcond_inlet_function(g, kind, node_map, custom_secondary_global, if_conv, if_turb0, if_turb1=0, if_scalar=0):
	
	# CPU-GPU transfers happen here becasue inlet BCs require Flow-aligned logic, thermodynamics, MPI-consistent
	# reductions

	time_module = custom_secondary_global["time_module"]
	time_st = time_module.time()
		
	# Unpack from the global dictionary
	numpy = custom_secondary_global["numpy"]
	secondary_functions = custom_secondary_global["secondary_functions"]
	ts_format = custom_secondary_global["ts_format"]
	cvars = custom_secondary_global["cvars"]
	ts_print = custom_secondary_global["ts_print"]
	math = custom_secondary_global["math"]
	MPI = custom_secondary_global["MPI"]
	mpi_comm = MPI.COMM_WORLD
	mpi_rank = mpi_comm.Get_rank()
	
	numba = custom_secondary_global["numba"]
	numba.cuda = custom_secondary_global["numba_cuda"]
	
	#ts_print("\nIn custom_bcond_inlet_function")
	
	cp = cvars["cp_main"]
	gamma = cvars["gamma_main"]
	rgas = cp - cp/gamma
   
	# bcond arrays in
	bcond_aname_in_list = ["pstag", "hstag", "vxfrac", "vyfrac", "vzfrac", "ref_frame", "turb0", "turb1", "scalar0", "group",
						   "ax", "ay", "az", "mirror_flag"]

	if "bcond_bcond_arrays_in" not in custom_secondary_global:
		bcond_arrays_in = {}
		custom_secondary_global["bcond_bcond_arrays_in"] = bcond_arrays_in
	else:
		bcond_arrays_in = custom_secondary_global["bcond_bcond_arrays_in"]

	for aname in bcond_aname_in_list:
		if aname not in bcond_arrays_in:
			a = g.get_bcond_array(kind, aname)
			bcond_arrays_in[aname] = a

	pstag_inlet_array = bcond_arrays_in["pstag"]
	hstag_inlet_array = bcond_arrays_in["hstag"]
	vxfrac_inlet_array = bcond_arrays_in["vxfrac"]
	vyfrac_inlet_array = bcond_arrays_in["vyfrac"]
	vzfrac_inlet_array = bcond_arrays_in["vzfrac"]
	ref_frame_inlet_array = bcond_arrays_in["ref_frame"]
	turb0_inlet_array = bcond_arrays_in["turb0"]
	turb1_inlet_array = bcond_arrays_in["turb1"]
	scalar0_inlet_array = bcond_arrays_in["scalar0"]
	group_inlet = bcond_arrays_in["group"]
	ax_array = bcond_arrays_in["ax"]
	ay_array = bcond_arrays_in["ay"]
	az_array = bcond_arrays_in["az"]

	aname_in_list = ["ro", "vx", "vy", "vz", "vrotx", "vroty", "vrotz",
					 "pstat", "hstag", "pstag", "turb0", "turb1", "scalar0"]

	if "bcond_arrays_in" not in custom_secondary_global:
		arrays_in = {}
		custom_secondary_global["bcond_arrays_in"] = arrays_in
	else:
		arrays_in = custom_secondary_global["bcond_arrays_in"]

	nnode = custom_secondary_global["nnode"]
	ngather = node_map.shape[0]
	
	if "node_map_d" not in arrays_in:
		node_map_d = numba.cuda.to_device(node_map)
		arrays_in["node_map_d"] = node_map_d
	else:
		node_map_d = arrays_in["node_map_d"]

	for aname in aname_in_list:
		if aname not in arrays_in:
			a = numpy.zeros(ngather, dtype=ts_format.np_float)
			a_d = numba.cuda.to_device(a)
			arrays_in[aname] = a
			arrays_in[aname + "_d"] = a_d
		else:
			a = arrays_in[aname]
			a_d = arrays_in[aname + "_d"]

		a_ptr = g.get_domain_array_ptr(aname)
		
		secondary_functions.gather_device_to_host(nnode, node_map_d, a_ptr, a_d, a)
		
	bcond_arrays_out = {}
	if if_conv == 0:
		bcond_aname_out_list = []
	else:
		bcond_aname_out_list = ["log_mass", "log_hstag", "log_pstag"]

	for aname in bcond_aname_out_list:
		a = g.get_bcond_array(kind, aname)
		bcond_arrays_out[aname] = a

	if "bcond_arrays_out" not in custom_secondary_global:
		arrays_out = {}
		custom_secondary_global["bcond_arrays_out"] = arrays_out
	else:
		arrays_out = custom_secondary_global["bcond_arrays_in"]


	aname_out_list = ["res_conv_ro", "res_conv_rovx", "res_conv_rovy", 
					   "res_conv_rovz", "res_conv_roe"]
	if if_turb0 == 1:
		aname_out_list = ["res_conv_turb0",]
		
	if if_turb1 == 1:
		aname_out_list = ["res_conv_turb0", "res_conv_turb1"]

	if if_scalar == 1:
		aname_out_list = ["res_conv_scalar0"]

	for aname in aname_out_list:
		if aname not in arrays_out:
			a = numpy.zeros(ngather, dtype=ts_format.np_float)
			a_d = numba.cuda.to_device(a)
			arrays_out[aname] = a
			arrays_out[aname + "_d"] = a_d
		else:
			a = arrays_out[aname]
			a_d = arrays_out[aname + "_d"]

   
	ro_domain_array = arrays_in["ro"]
	vx_domain_array = arrays_in["vx"]
	vy_domain_array = arrays_in["vy"]
	vz_domain_array = arrays_in["vz"]
	vrotx_domain_array = arrays_in["vrotx"]
	vroty_domain_array = arrays_in["vroty"]
	vrotz_domain_array = arrays_in["vrotz"]
	pstat_domain_array = arrays_in["pstat"]
	hstag_domain_array = arrays_in["hstag"]
	pstag_domain_array = arrays_in["pstag"]
	

	if if_turb0 == 1:
		turb0_domain_array = arrays_in["turb0"]

	if if_turb1 == 1:
		turb1_domain_array = arrays_in["turb1"]

	if if_scalar == 1:
		scalar0_domain_array = arrays_in["scalar0"]

	# domain arrays out
	if if_conv == 1:
		res_ro_array = arrays_out["res_conv_ro_d"]
		res_rovx_array = arrays_out["res_conv_rovx_d"]
		res_rovy_array = arrays_out["res_conv_rovy_d"]
		res_rovz_array = arrays_out["res_conv_rovz_d"]
		res_roe_array = arrays_out["res_conv_roe_d"]

		log_mass_array = bcond_arrays_out["log_mass"]
		log_hstag_array = bcond_arrays_out["log_hstag"]
		log_pstag_array = bcond_arrays_out["log_pstag"]

	if if_turb0 == 1:
		res_turb0_array = arrays_out["res_conv_turb0_d"]

	if if_turb1 == 1:
		res_turb1_array = arrays_out["res_conv_turb1_d"]

	if if_scalar == 1:
		res_scalar0_array = arrays_out["res_conv_scalar0_d"]


	# rotating domain velocity
	vrotx = vrotx_domain_array
	vroty = vroty_domain_array
	vrotz = vrotz_domain_array

	# TODO this is where we can prescribe the mass flow rate

	# inlet conditions (velocity magnitude interpolated from domain)
	v_inlet = numpy.sqrt(vx_domain_array*vx_domain_array + vy_domain_array*vy_domain_array + vz_domain_array*vz_domain_array)
	vrel_inlet = numpy.sqrt((vx_domain_array-vrotx)*(vx_domain_array-vrotx) + (vy_domain_array-vroty)*(vy_domain_array-vroty) + (vz_domain_array-vrotz)*(vz_domain_array-vrotz))

	# if specified in absolute frame 
	ref_frame_inlet = ref_frame_inlet_array

	if (len(ref_frame_inlet) > 0) and (ref_frame_inlet[0] == 0):
		vx_inlet = v_inlet*vxfrac_inlet_array
		vy_inlet = v_inlet*vyfrac_inlet_array
		vz_inlet = v_inlet*vzfrac_inlet_array
	# if specified in absolute frame 
	else:
		vx_inlet = vrel_inlet*vxfrac_inlet_array + vrotx
		vy_inlet = vrel_inlet*vyfrac_inlet_array + vroty
		vz_inlet = vrel_inlet*vzfrac_inlet_array + vrotz

	pstag_inlet = pstag_inlet_array
	hstag_inlet = hstag_inlet_array
	hstat_inlet = numpy.maximum(hstag_inlet - 0.5*v_inlet*v_inlet, 0)
	tstat_inlet = hstat_inlet/cp
	tstag_inlet = hstag_inlet/cp 
	pstat_inlet = pstag_inlet_array*((tstat_inlet/tstag_inlet)**(gamma/(gamma-1)))
	rostat_inlet = pstat_inlet/(rgas*tstat_inlet)
	
	if if_turb0 == 1:
		turb0_inlet = turb0_inlet_array

	if if_turb1 == 1:
		turb1_inlet = turb1_inlet_array

	if if_scalar == 1:
		scalar0_inlet = rostat_inlet*scalar0_inlet_array
		
	# Custom inlet code now finished
	# Set the calculated variables at _c onto the inlet condition as required

	# final inlet conditions
	ro_array_0 = rostat_inlet

	vx_array_0 = vx_inlet

	vy_array_0 = vy_inlet

	vz_array_0 = vz_inlet

	pstat_array_0 = pstat_inlet

	hstag_array_0 = hstag_inlet

	pstag_array_0 = pstag_inlet

	vrotx_array_0 = vrotx_domain_array

	vroty_array_0 = vroty_domain_array

	vrotz_array_0 = vrotz_domain_array

	if if_turb0 == 1:
		turb0_array_0 = turb0_inlet

	if if_turb1 == 1:
		turb1_array_0 = turb1_inlet

	if if_scalar == 1:
		scalar0_array_0 = scalar0_inlet

	ro_array_1 = ro_domain_array

	vx_array_1 = vx_domain_array

	vy_array_1 = vy_domain_array

	vz_array_1 = vz_domain_array

	vrotx_array_1 = vrotx_domain_array

	vroty_array_1 = vroty_domain_array

	vrotz_array_1 = vrotz_domain_array

	pstat_array_1 = pstat_domain_array

	hstag_array_1 = hstag_domain_array

	pstag_array_1 = pstag_domain_array

	if if_turb0 == 1:
		turb0_array_1 = turb0_domain_array

	if if_turb1 == 1:
		turb1_array_1 = turb1_domain_array

	if if_scalar == 1:
		scalar0_array_1 = scalar0_domain_array

	ro_avg = 0.5*(ro_array_0 + ro_array_1)

	vx_avg = 0.5*(vx_array_0 + vx_array_1)

	vy_avg = 0.5*(vy_array_0 + vy_array_1)

	vz_avg = 0.5*(vz_array_0 + vz_array_1)

	vrotx_avg = 0.5*(vrotx_array_0 + vrotx_array_1)

	vroty_avg = 0.5*(vroty_array_0 + vroty_array_1)
	vrotz_avg = 0.5*(vrotz_array_0 + vrotz_array_1)

	vrelx_avg = vx_avg - vrotx_avg

	vrely_avg = vy_avg - vroty_avg

	vrelz_avg = vz_avg - vrotz_avg

	pstat_avg = 0.5*(pstat_array_0 + pstat_array_1)

	hstag_avg = 0.5*(hstag_array_0 + hstag_array_1)

	pstag_avg = 0.5*(pstag_array_0 + pstag_array_1)

	if if_turb0 == 1:
		turb0_avg = 0.5*(turb0_array_0 + turb0_array_1)

	if if_turb1 == 1:
		turb1_avg = 0.5*(turb1_array_0 + turb1_array_1)

	if if_scalar == 1:
		scalar_avg = 0.5*(scalar0_array_0 + scalar0_array_1)

	flux_ro = ro_avg*vrelx_avg*ax_array + ro_avg*vrely_avg*ay_array + ro_avg*vrelz_avg*az_array

	flux_ro = numpy.maximum(0, flux_ro)

	flux_rovx = flux_ro*vx_avg + pstat_avg*ax_array

	flux_rovy = flux_ro*vy_avg + pstat_avg*ay_array

	flux_rovz = flux_ro*vz_avg + pstat_avg*az_array

	flux_roe = flux_ro*hstag_avg + pstat_avg*(vrotx_avg*ax_array + vroty_avg*ay_array + vrotz_avg*az_array)

	if if_turb0 == 1:
		flux_turb0 = turb0_avg*vrelx_avg*ax_array + turb0_avg*vrely_avg*ay_array + turb0_avg*vrelz_avg*az_array

	if if_turb1 == 1:
		flux_turb1 = turb1_avg*vrelx_avg*ax_array + turb1_avg*vrely_avg*ay_array + turb1_avg*vrelz_avg*az_array

	if if_scalar == 1:
		flux_scalar = scalar_avg*vrelx_avg*ax_array + scalar_avg*vrely_avg*ay_array + scalar_avg*vrelz_avg*az_array


	if if_conv == 1:
		
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_ro"), res_ro_array, -flux_ro)
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_rovx"), res_rovx_array, -flux_rovx)
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_rovy"), res_rovy_array, -flux_rovy)
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_rovz"), res_rovz_array, -flux_rovz)
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_roe"), res_roe_array, -flux_roe)
		

	if if_turb0 == 1:
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_turb0"), res_turb0_array, -flux_turb0)
		
	if if_turb1 == 1:
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_turb1"), res_turb1_array, -flux_turb1)
		
	if if_scalar == 1:
		secondary_functions.scatter_host_to_device(nnode, node_map_d, g.get_domain_array_ptr("res_conv_scalar0"), res_scalar0_array, -flux_scalar)
		

	if if_conv == 1:
		mirror_flag_mul = 1
		log_mass_array += flux_ro*mirror_flag_mul
		log_hstag_array += flux_ro*hstag_avg*mirror_flag_mul
		log_pstag_array += flux_ro*pstag_avg*mirror_flag_mul

   
	for aname in bcond_aname_out_list:
		g.set_bcond_array(kind, aname, bcond_arrays_out[aname])

	mpi_comm.Barrier()
	time_en = time_module.time()