from mpi4py import MPI

import math
import numpy
import sys
from numba import njit, prange
import numba
import numba.cuda

# from contrails import hygrometry


def ts_print(*args):
    mpi_rank = MPI.COMM_WORLD.Get_rank()

    if mpi_rank == 0:
        print(" ".join(map(str,args)))
        
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

def mpi_reduce_array(a, op=MPI.MAX):
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    # Determine the neutral element based on the operation
    if op == MPI.SUM:
        neutral_value = 0
    elif op == MPI.MAX:
        neutral_value = -math.inf
    elif op == MPI.MIN:
        neutral_value = math.inf
    else:
        raise ValueError("Unsupported MPI operation")

    # If the scalar is None, set it to the neutral value for the reduction
    if len(a) == 0:
        scalar = neutral_value
        participation_flag = 0
    else:
        if op == MPI.MAX:
            scalar = a.max()
        elif op == MPI.MIN:
            scalar = a.min()
        else:
            print("Unsupported operation")
            sys.exit()
        participation_flag = 1

    # First, perform an allreduce to determine if any rank has a valid value
    participation_flags = comm.allreduce(participation_flag, op=MPI.SUM)

    if participation_flags == 0:
        # No ranks are participating, return None
        return None

    # Perform the reduction
    reduced_scalar = comm.allreduce(scalar, op=op)

    
    return reduced_scalar

def mpi_mean(local_array):
    # Get the MPI communicator
    comm = MPI.COMM_WORLD

    # Calculate local sum and count
    local_sum = numpy.sum(local_array)
    local_count = len(local_array)


    # Perform the Allreduce to sum the local sums and counts across all ranks
    global_sum = comm.allreduce(local_sum, op=MPI.SUM)
    global_count = comm.allreduce(local_count, op=MPI.SUM)

    # Calculate the global mean
    if global_count > 0:
        global_mean = global_sum / global_count
    else:
        global_mean = None  # Handle the case where no data is present

    return global_mean


@numba.cuda.jit
def gather_device_to_host_kernel(node_map, a, b):
    i = numba.cuda.grid(1)
    
    if i < node_map.size:
        b[i] = a[node_map[i]]

def gather_device_to_host(nnode, node_map, a_ptr, b_d, b_h):
    ngather = b_h.shape[0]
    if ngather == 0:
        return
    a_d = cuda_ptr_to_numpy_array(nnode, a_ptr)
    
    threads_per_block = 256
    blocks_per_grid = (ngather + (threads_per_block - 1)) // threads_per_block
    
   
    gather_device_to_host_kernel[blocks_per_grid, threads_per_block](node_map, a_d, b_d)
    numba.cuda.synchronize()
    b_d.copy_to_host(b_h)

@numba.cuda.jit
def scatter_host_to_device_kernel(node_map, a, b):
    i = numba.cuda.grid(1)
    
    if i < node_map.size:
        numba.cuda.atomic.add(a, node_map[i], b[i])

def scatter_host_to_device(nnode, node_map, a_ptr, b_d, b_h):
    
    nscatter = b_h.shape[0]
    if nscatter == 0:
        return
    a_d = cuda_ptr_to_numpy_array(nnode, a_ptr)
    
    b_d.copy_to_device(b_h)
    threads_per_block = 256
    blocks_per_grid = (nscatter + (threads_per_block - 1)) // threads_per_block
    
  
    scatter_host_to_device_kernel[blocks_per_grid, threads_per_block](node_map, a_d, b_d)
    numba.cuda.synchronize()

def moment(m0,m1,m2):
    return

@numba.cuda.jit
def set_secondary_microphsics_kernel(gamma, cp, visc_lam,time_step, vol,
                                     x_in, y_in, z_in, ro_in, rovx_in, rovy_in, rovz_in, roe_in,
                                     idomain_in, omega_in,
                                     scalar0_in, scalar1_in, scalar2_in,
                                     
                                     scalarnd0_out, scalarnd1_out, scalarnd2_out,
                                     ro_src_out, rovx_src_out, rovy_src_out, rovz_src_out, roe_src_out,
                                     scalar0_src_out, scalar1_src_out, scalar2_src_out,

                                     vx_out, vy_out, vz_out, vrotx_out, vroty_out, vrotz_out,
                                     tstat_out, pstat_out, pstag_out, hstag_out, tstag_out,
                                     viscosity_laminar_out, asound_out,

                                     fit_p,fit_T,fit_a,fit_b,fit_m0,fit_gamma,fit_delta,
                                     ):
    i = numba.cuda.grid(1)

    if i < x_in.size:
        # get the rotational velocity from the domain
        idomain = idomain_in[i]

        omega = omega_in[idomain]

        omegax = omega
        omegay = numba.float32(0.0)
        omegaz = numba.float32(0.0)
        x = x_in[i]
        y = y_in[i]
        z = z_in[i]

        vrotx = numba.float32(0.0)
        vroty = -omegax * z
        vrotz = omegax * y

        vx = rovx_in[i] / ro_in[i]
        vy = rovy_in[i] / ro_in[i]
        vz = rovz_in[i] / ro_in[i]

        # CODE HERE
        cv=cp/gamma
        rgas=cp-cv
        rvap=8.3145/18.02
        eke = 0.5 * (vx * vx + vy * vy + vz * vz)
        tstat = (roe_in[i] / ro_in[i] - eke) / cv
        tstag = tstat + eke / cp
        hstag = cp * tstag
        asound = math.sqrt(gamma * rgas * tstat)
        pstat = ro_in[i] * rgas * tstat
        pstag = pstat * math.pow(tstag / tstat, gamma / (gamma - 1.0))

        ew = math.exp(-6096.9385 / tstat + 21.2409642 - 2.711193e-2 * tstat + 1.673952e-5 * tstat ** 2 + 2.433502 * math.log(tstat))
        ei = math.exp(-6024.528211 / tstat + 29.32707 + 1.0613868e-2 * tstat + -1.3198825e-5 * tstat ** 2 - 0.49382577 * math.log(tstat))
        f = 1.0016 + 3.15e-8 * pstat - 7.4e-4 / pstat
        psat_water = ew * f
        psat_ice = ei * f

        # computational conversion - ro not physical - todo
        n = max(1,scalar0_in[i])
        rhov = max(0,scalar1_in[i])
        rhol = max(0,scalar2_in[i])

        Yvap = rhov/ro_in[i]
        p_h2o = Yvap / (1 - Yvap) * pstat * 28.96 / 18.02

        # model constants
        p_c=(pstat-fit_p[0])/(fit_p[-1]-fit_p[0])*(fit_p.size-1)
        p_c=max(min(p_c,fit_p.size-1),0)
        t_c=(tstat-fit_T[0])/(fit_T[-1]-fit_T[0])*(fit_T.size-1)
        t_c=max(min(t_c,fit_T.size-1),0)
        p_f,p_i = math.modf(p_c)
        T_f,T_i = math.modf(t_c)

        a = fit_a[int(p_i),int(T_i)]*(1-p_f)*(1-T_f) + fit_a[int(p_i)+1,int(T_i)]*p_f*(1-T_f) + fit_a[int(p_i),int(T_i)+1]*(1-p_f)*T_f + fit_a[int(p_i)+1,int(T_i)+1]*p_f*T_f
        b = fit_b[int(p_i),int(T_i)]*(1-p_f)*(1-T_f) + fit_b[int(p_i)+1,int(T_i)]*p_f*(1-T_f) + fit_b[int(p_i),int(T_i)+1]*(1-p_f)*T_f + fit_b[int(p_i)+1,int(T_i)+1]*p_f*T_f

        rowater = 1000
        tsig = 647.096
        kappa=0.9
        rd=20e-9

        sigma_wa = 235.8*(1-tstat/tsig)**1.256*(1-0.625*(1-tstat/tsig))
        ak = 2 * sigma_wa / (rvap*tstat*rowater)
        x = 3 * kappa * rd / ak
        rstar = rd * (1 + x**(1/2)*(x**(2/3)+1)/(x**(2/3)+3))
        aw = (rstar ** 3 - rd ** 3) / (rstar ** 3 - rd ** 3 * (1 - kappa))

        logSstar = (ak/rstar)**aw
        mstar = 4/3*3.1415926*(rstar**3-rd**3)*rowater # todo account for core mass
        mdefecit = n*mstar - rhol

        # nucleation
        condensing = (0 < mdefecit < rhov) and (math.log(max(p_h2o / psat_water, 1e-20)) > logSstar)

        rhov -= condensing * mdefecit
        rhol += condensing * mdefecit

        # growth
        e_fac = (psat_water/psat_ice>1.01) * (p_h2o-psat_ice) / (psat_water-psat_ice)
        S = e_fac * n * a * (rhol/n) ** b

        # write out
        scalarnd0_out[i] = n/ro_in[i]
        scalarnd1_out[i] = rhov/ro_in[i]
        scalarnd2_out[i] = rhol/ro_in[i]

        scalar0_in[i] = n
        scalar1_in[i] = rhov
        scalar2_in[i] = rhol

        scalar1_src_out[i] = 0*(not condensing) * -S
        scalar2_src_out[i] = 0*(not condensing) *  S

        vrotx_out[i] = vrotx
        vroty_out[i] = vroty
        vrotz_out[i] = vrotz
        vx_out[i] = vx
        vy_out[i] = vy
        vz_out[i] = vz

        tstat_out[i] = tstat
        pstat_out[i] = pstat
        hstag_out[i] = hstag
        pstag_out[i] = pstag
        tstag_out[i] = tstag
        viscosity_laminar_out[i] = numba.float32(visc_lam)
        asound_out[i] = asound

@numba.cuda.jit
def set_secondary_kernel(gamma_main, gamma_cooling, cp_main, cp_cooling, visc_lam, x_in, y_in, z_in, ro_in, rovx_in, rovy_in, rovz_in, roe_in, scalar0_in, idomain_in, omega_in, vx_out, vy_out, vz_out, vrotx_out, vroty_out, vrotz_out, tstat_out, pstat_out, pstag_out, hstag_out, tstag_out, viscosity_laminar_out, asound_out):
    
    i = numba.cuda.grid(1)
    
    
    if i < x_in.size:
        # get the rotational velocity from the domain
        idomain = idomain_in[i]
        
        omega = omega_in[idomain]
        
        omegax = omega
        omegay = numba.float32(0.0)
        omegaz = numba.float32(0.0)
        x = x_in[i]
        y = y_in[i]
        z = z_in[i]

        vrotx = numba.float32(0.0)
        vroty = -omegax*z
        vrotz = omegax*y
        
        vx = rovx_in[i]/ro_in[i]
        vy = rovy_in[i]/ro_in[i]
        vz = rovz_in[i]/ro_in[i]


        # get scalar and clamp it
        scalar = scalar0_in[i]/ro_in[i]
        scalar = max(0.0, scalar)
        scalar = min(1.0, scalar)
        
        cv_main = cp_main/gamma_main
        cv_cooling = cp_cooling/gamma_cooling
        
        cp_mix = (1-scalar)*cp_main + scalar*cp_cooling
        cv_mix = (1-scalar)*cv_main + scalar*cv_cooling
        rgas_mix = cp_mix - cv_mix
        gamma_mix = cp_mix/cv_mix
        

        eke = 0.5*(vx*vx + vy*vy + vz*vz)
        tstat = (roe_in[i]/ro_in[i] - eke)/cv_mix
        tstag = tstat + eke/cp_mix
        hstag = cp_mix*tstag
        asound = math.sqrt(gamma_mix*rgas_mix*tstat)
        pstat = ro_in[i]*rgas_mix*tstat
        pstag = pstat*math.pow(tstag/tstat, gamma_mix/(gamma_mix-1.0))



        vrotx_out[i] = vrotx
        vroty_out[i] = vroty
        vrotz_out[i] = vrotz
        vx_out[i] = vx
        vy_out[i] = vy
        vz_out[i] = vz

        tstat_out[i] = tstat
        pstat_out[i] = pstat
        hstag_out[i] = hstag
        pstag_out[i] = pstag
        tstag_out[i] = tstag
        viscosity_laminar_out[i] = numba.float32(visc_lam)
        asound_out[i] = asound



# Simple secondary kernel that calculates just the pressure 
# TODO: ASK TOBIAS - I DON'T actually need this right? Since TS solver already computes secondary variables
# like pstat per time step, so I just need to do g.get_domain_array_ptr("pstat") in the custom_secondary_function.
@numba.cuda.jit
def set_secondary_wing_force_kernel(gamma, cp,time_step, vol,
                                     x_in, y_in, z_in, ro_in, rovx_in, rovy_in, rovz_in, roe_in,
                                     idomain_in, omega_in,
                                     
                                     vx_out, vy_out, vz_out, vrotx_out, vroty_out, vrotz_out,
                                     tstat_out, pstat_out, pstag_out, hstag_out, tstag_out,
                                     asound_out,
                                    ):
    
    # N.B. many of the inputs and outputs above are actually redundant for now, I left them in unused
    # just in case we need them in the future, but I doubt I need them for what I'm doing - extracting
    # pressure pstat off surface of wing.

    i = numba.cuda.grid(1) # computes global thread index across whole launch, 1 means 1D kernel
    # so each thread gets a unique integer i covering: 0,1,2, ...,blocks_per_grid * threads_per_block -1

    if i < x_in.size:
        #===================
        # Standard code from TS, don't change
        #===================
        # get the rotational velocity from the domain
        idomain = idomain_in[i]

        omega = omega_in[idomain]

        omegax = omega
        omegay = numba.float32(0.0)
        omegaz = numba.float32(0.0)
        x = x_in[i]
        y = y_in[i]
        z = z_in[i]

        vrotx = numba.float32(0.0)
        vroty = -omegax * z
        vrotz = omegax * y

        vx = rovx_in[i] / ro_in[i]
        vy = rovy_in[i] / ro_in[i]
        vz = rovz_in[i] / ro_in[i]


        #===============================
        # Start CODING IN THIS SECTIONS
        #===============================
        # tbh I prob don't even need some of these like hstag, asound and pstag
        cv = cp/gamma
        rgas = cp - cv
        eke = 0.5 * (vx * vx + vy * vy + vz * vz)
        tstat = (roe_in[i] / ro_in[i] - eke) / cv
        tstag = tstat + eke / cp
        hstag = cp * tstag
        asound = math.sqrt(gamma * rgas * tstat)
        pstat = ro_in[i] * rgas * tstat
        pstag = pstat * math.pow(tstag / tstat, gamma / (gamma - 1.0))


        #================
        # Write out
        #================
        vrotx_out[i] = vrotx
        vroty_out[i] = vroty
        vrotz_out[i] = vrotz
        vx_out[i] = vx
        vy_out[i] = vy
        vz_out[i] = vz

        tstat_out[i] = tstat
        pstat_out[i] = pstat
        hstag_out[i] = hstag
        pstag_out[i] = pstag
        tstag_out[i] = tstag
        asound_out[i] = asound





def cuda_ptr_to_numpy_array(nnode, ptr, dtype=numpy.float32):
    import ctypes
   
    ctypes_ptr = ctypes.c_void_p(ptr)
    ctx = numba.cuda.current_context()
    element_size = numpy.dtype(dtype).itemsize
    size_in_bytes = nnode * element_size
    memptr = numba.cuda.cudadrv.driver.MemoryPointer(ctx, ctypes_ptr, size=size_in_bytes)
    shape = (nnode,)
    strides = (element_size,)
    a_d = numba.cuda.cudadrv.devicearray.DeviceNDArray(shape=shape, strides=strides, dtype=dtype, gpu_data=memptr)
    numba.cuda.synchronize()
    return a_d

def set_secondary(nnode, ndom, x_ptr, y_ptr, z_ptr, time_step_ptr,vol_ptr,
                  ro_ptr, rovx_ptr, rovy_ptr, rovz_ptr, roe_ptr,
                  scalar0_ptr, scalar1_ptr, scalar2_ptr,
                  scalarnd0_ptr, scalarnd1_ptr, scalarnd2_ptr,
                  ro_src_ptr, rovx_src_ptr, rovy_src_ptr, rovz_src_ptr, roe_src_ptr,
                  scalar0_src_ptr, scalar1_src_ptr, scalar2_src_ptr,
                  idomain_ptr, omega_ptr,
                  vx_ptr, vy_ptr, vz_ptr, vrotx_ptr, vroty_ptr, vrotz_ptr,
                  tstat_ptr, pstat_ptr, pstag_ptr, hstag_ptr, tstag_ptr,
                  viscosity_laminar_ptr, asound_ptr, csg):
    time_module = csg["time_module"]
    ts_format = csg["ts_format"]
    numpy = csg["numpy"]
    ts_print = csg["ts_print"]
    MPI = csg["MPI"]
    cvars = csg["cvars"]
    
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()
    mpi_size = mpi_comm.Get_size()

    if "numba" not in csg:
        import numba
        import numba.cuda
        csg["numba"] = numba
        csg["numba_cuda"] = numba.cuda
        ngpu = len(numba.cuda.gpus)
        numba.cuda.select_device(mpi_rank%ngpu)

    numba = csg["numba"]
    numba.cuda = csg["numba_cuda"]
    
    
    # wrap ptrs into arrays
    x_d = cuda_ptr_to_numpy_array(nnode, x_ptr)    
    y_d = cuda_ptr_to_numpy_array(nnode, y_ptr)
    z_d = cuda_ptr_to_numpy_array(nnode, z_ptr)
    time_step_d = cuda_ptr_to_numpy_array(nnode, time_step_ptr)
    vol_d = cuda_ptr_to_numpy_array(nnode, vol_ptr)
    
    ro_d = cuda_ptr_to_numpy_array(nnode, ro_ptr)
    rovx_d = cuda_ptr_to_numpy_array(nnode, rovx_ptr)
    rovy_d = cuda_ptr_to_numpy_array(nnode, rovy_ptr)
    rovz_d = cuda_ptr_to_numpy_array(nnode, rovz_ptr)
    roe_d = cuda_ptr_to_numpy_array(nnode, roe_ptr)
    
    scalar0_d = cuda_ptr_to_numpy_array(nnode, scalar0_ptr)
    scalar1_d = cuda_ptr_to_numpy_array(nnode, scalar1_ptr)
    scalar2_d = cuda_ptr_to_numpy_array(nnode, scalar2_ptr)
    scalarnd0_d = cuda_ptr_to_numpy_array(nnode, scalarnd0_ptr)
    scalarnd1_d = cuda_ptr_to_numpy_array(nnode, scalarnd1_ptr)
    scalarnd2_d = cuda_ptr_to_numpy_array(nnode, scalarnd2_ptr)
    
    ro_src_d = cuda_ptr_to_numpy_array(nnode, ro_src_ptr)
    rovx_src_d = cuda_ptr_to_numpy_array(nnode, rovx_src_ptr)
    rovy_src_d = cuda_ptr_to_numpy_array(nnode, rovy_src_ptr)
    rovz_src_d = cuda_ptr_to_numpy_array(nnode, rovz_src_ptr)
    roe_src_d = cuda_ptr_to_numpy_array(nnode, roe_src_ptr)
    scalar0_src_d = cuda_ptr_to_numpy_array(nnode, scalar0_src_ptr)
    scalar1_src_d = cuda_ptr_to_numpy_array(nnode, scalar1_src_ptr)
    scalar2_src_d = cuda_ptr_to_numpy_array(nnode, scalar2_src_ptr)
    
    idomain_d = cuda_ptr_to_numpy_array(nnode, idomain_ptr, dtype=numpy.int64)
    omega_d = cuda_ptr_to_numpy_array(ndom, omega_ptr)

    
    vx_d = cuda_ptr_to_numpy_array(nnode, vx_ptr)
    vy_d = cuda_ptr_to_numpy_array(nnode, vy_ptr)
    vz_d = cuda_ptr_to_numpy_array(nnode, vz_ptr)
    vrotx_d = cuda_ptr_to_numpy_array(nnode, vrotx_ptr)
    vroty_d = cuda_ptr_to_numpy_array(nnode, vroty_ptr)
    vrotz_d = cuda_ptr_to_numpy_array(nnode, vrotz_ptr)
    tstat_d = cuda_ptr_to_numpy_array(nnode, tstat_ptr)
    pstat_d = cuda_ptr_to_numpy_array(nnode, pstat_ptr)
    pstag_d = cuda_ptr_to_numpy_array(nnode, pstag_ptr)
    hstag_d = cuda_ptr_to_numpy_array(nnode, hstag_ptr)
    tstag_d = cuda_ptr_to_numpy_array(nnode, tstag_ptr)
    viscosity_laminar_d = cuda_ptr_to_numpy_array(nnode, viscosity_laminar_ptr)
    asound_d = cuda_ptr_to_numpy_array(nnode, asound_ptr)

    # remove microphysics ice growth parameters, not needed for me
    # a_d = csg['fit_a_d']
    # b_d = csg['fit_b_d']
    # m0_d = csg['fit_m0_d']
    # gamma_d = csg['fit_gamma_d']
    # delta_d = csg['fit_delta_d']
    # p_d = csg['fit_p_d']
    # T_d = csg['fit_T_d']
    
    cp_main = cvars["cp_main"]
    gamma_main = cvars["gamma_main"]
    cp_cooling = cvars["cp_cooling"]
    gamma_cooling = cvars["gamma_cooling"]
    visc_lam = cvars["visc_lam"]
    
    # call the kernel 
    threads_per_block = 256
    blocks_per_grid = (nnode + (threads_per_block - 1)) // threads_per_block
    # set_secondary_kernel[blocks_per_grid, threads_per_block](gamma_main, gamma_cooling, cp_main, cp_cooling, visc_lam, x_d, y_d, z_d, ro_d, rovx_d, rovy_d, rovz_d, roe_d, scalar0_d, idomain_d, omega_d, vx_d, vy_d, vz_d, vrotx_d, vroty_d, vrotz_d, tstat_d, pstat_d, pstag_d, hstag_d, tstag_d, viscosity_laminar_d, asound_d)
    
    # replace set_secondary_microphsics_kernel with one that extracts pressure on wing surface
    # set_secondary_microphsics_kernel[blocks_per_grid, threads_per_block](gamma_main, cp_main, visc_lam, time_step_d, vol_d,
    #                                  x_d, y_d, z_d, ro_d, rovx_d, rovy_d, rovz_d, roe_d,
    #                                  idomain_d, omega_d,
    #                                  scalar0_d, scalar1_d, scalar2_d,
    #                                  scalarnd0_d, scalarnd1_d, scalarnd2_d,
    #                                  ro_src_d, rovx_src_d, rovy_src_d, rovz_src_d, roe_src_d,
    #                                  scalar0_src_d, scalar1_src_d, scalar2_src_d,
    #                                  vx_d, vy_d, vz_d, vrotx_d, vroty_d, vrotz_d,
    #                                  tstat_d, pstat_d, pstag_d, hstag_d, tstag_d,
    #                                  viscosity_laminar_d, asound_d,
    #                                  p_d,T_d,a_d,b_d,m0_d,gamma_d,delta_d
    # )

    

    numba.cuda.synchronize()


  
    return

