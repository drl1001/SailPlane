import numpy as np
import paraview
from paraview.simple import *
import paraview.servermanager as sm
import matplotlib.pyplot as plt
import vtk


# def PVDataToNumpy(data, points=False):
#     '''
#     Kailen code
#     Function that converts paraview data into a dictionary of numpy arrays for easier subsequent calculation.
 
#     parameters:
#     -----------
#         data: proxy
#             paraview object
#         points: bool
#             True also appends the point coordinate array
 
#     returns:
#     -----------
#         data_arrays: dictionary
#             dictionary with keys corresponding to point data arrays. Array data given as numpy arrays.
#     '''
#     #Fetch data using server manager
#     polydata = sm.Fetch(data)
#     print(f'Extracted data type: {polydata}')
#     print(f'Class name: {polydata.GetClassName()}')
#     print(f'number of blocks: {polydata.GetNumberOfBlocks()}')
 
#     #Get Point Data
#     try:
#         pdat = polydata.GetPointData()
#     except:
#         try: 
#             block = polydata.GetBlock(0)
#             pdat = block.GetRowData()
#         except:
#             raise NameError('This data type cannot be converted')
#     #Iterate over point data to collect array names and arrays
#     data_arrays = {}
#     n_arr = pdat.GetNumberOfArrays()
#     for i in range(n_arr):
#         name = pdat.GetArrayName(i)
#         arr = np.array(pdat.GetArray(i))
#         data_arrays[name] = arr
#     #Get point coordinates if required
#     if points:
#         pts = polydata.GetPoints()
#         npoints = pts.GetNumberOfPoints()
#         dat = np.zeros((npoints, 3))
#         for i in range(npoints):
#             dat[i,:] = np.array(pts.GetPoint(i))
#         data_arrays["Points"] = dat
 
#     return data_arrays

def PVDataToNumpy(data, points=False, target_probe_name=None):
    '''
    Function that converts paraview data into a dictionary of numpy arrays.
    '''
    # Fetch data using server manager
    polydata = sm.Fetch(data)
    print(f'Extracted data type: {polydata.GetClassName()}')
    print(f'Number of blocks: {polydata.GetNumberOfBlocks()}')
    
    data_arrays = {}
    
    # Handle MultiBlock dataset
    if polydata.GetClassName() == 'vtkMultiBlockDataSet':
        # Find the correct block
        block_index = 0
        if target_probe_name:
            for i in range(polydata.GetNumberOfBlocks()):
                block = polydata.GetBlock(i)
                meta = polydata.GetMetaData(i)
                if meta and target_probe_name in meta.Get(vtk.vtkCompositeDataSet.NAME()):
                    block_index = i
                    print(f"Using block {i} for probe: {target_probe_name}")
                    break
        
        if polydata.GetNumberOfBlocks() <= block_index:
            print(f"Warning: Block index {block_index} is out of range. Using first available block.")
            block_index = 0
        
        # Get the specific block we want
        block = polydata.GetBlock(block_index)
        if block is None:
            raise NameError(f'Block {block_index} is None')
        
        print(f'Using block {block_index}: {block.GetClassName()}')
        
        # Get Point Data from the block
        if hasattr(block, 'GetPointData'):
            pdat = block.GetPointData()
            n_arr = pdat.GetNumberOfArrays()
            print(f'Number of point data arrays: {n_arr}')
            
            for i in range(n_arr):
                name = pdat.GetArrayName(i)
                arr = np.array(pdat.GetArray(i))
                data_arrays[name] = arr
                print(f'  Added array: {name} with shape {arr.shape}')
        else:
            print('Warning: Block does not have point data')
        
        # Get point coordinates if required
        if points and hasattr(block, 'GetPoints'):
            pts = block.GetPoints()
            if pts:
                npoints = pts.GetNumberOfPoints()
                dat = np.zeros((npoints, 3))
                for i in range(npoints):
                    dat[i,:] = np.array(pts.GetPoint(i))
                data_arrays["Points"] = dat
                print(f'Added Points array with shape {dat.shape}')
    
    # Handle single dataset (non-multiblock)
    elif hasattr(polydata, 'GetPointData'):
        pdat = polydata.GetPointData()
        n_arr = pdat.GetNumberOfArrays()
        for i in range(n_arr):
            name = pdat.GetArrayName(i)
            arr = np.array(pdat.GetArray(i))
            data_arrays[name] = arr
        
        if points and hasattr(polydata, 'GetPoints'):
            pts = polydata.GetPoints()
            npoints = pts.GetNumberOfPoints()
            dat = np.zeros((npoints, 3))
            for i in range(npoints):
                dat[i,:] = np.array(pts.GetPoint(i))
            data_arrays["Points"] = dat
 
    else:
        raise NameError(f'This data type ({polydata.GetClassName()}) cannot be converted')
 
    return data_arrays



#     return cellDatatoPointData1
def calc_cell_props(filename: str, probe_name: str):
    '''
    Simple approach - apply filters to the entire dataset and extract later
    '''
    print(f"Loading file: {filename}")
    
    # create a new 'XDMF Reader'
    probe_outxdmf = XDMFReader(registrationName='probe_out.xdmf', FileNames=[filename])
    UpdatePipeline()
    
    # Apply all filters to the entire dataset
    extractSurface1 = ExtractSurface(registrationName='ExtractSurface1', Input=probe_outxdmf)
    UpdatePipeline()
    
    surfaceNormals1 = SurfaceNormals(registrationName='SurfaceNormals1', Input=extractSurface1)
    UpdatePipeline()
    
    cellSize1 = CellSize(registrationName='CellSize1', Input=surfaceNormals1)
    UpdatePipeline()
    
    cellDatatoPointData1 = CellDatatoPointData(registrationName='CellDatatoPointData1', Input=cellSize1)
    cellDatatoPointData1.CellDataArraytoprocess = ['Area']
    UpdatePipeline()

    return cellDatatoPointData1
# ========================
# FOR DEBUGGIN !
# ========================
# def calc_cell_props(filename: str, probe_name: str):
#     '''
#     Extract calculator1 which contains the cell Normals, cell Area
#     '''
#     print(f"Loading file: {filename}")
#     print(f"Looking for probe: {probe_name}")
    
#     # create a new 'XDMF Reader'
#     probe_outxdmf = XDMFReader(registrationName='probe_out.xdmf', FileNames=[filename])
    
#     # Update the reader FIRST to load data
#     UpdatePipeline()
#     print(f"XDMF Reader timesteps: {probe_outxdmf.TimestepValues}")
    
#     # Check what blocks are available
#     print("Available blocks:")
#     if hasattr(probe_outxdmf, 'BlockInfo'):
#         print(probe_outxdmf.BlockInfo)
    
#     # Try different selector patterns
#     extractBlock1 = ExtractBlock(registrationName='ExtractBlock1', Input=probe_outxdmf)
    
#     # Print available selectors
#     print("Available selectors:")
#     if hasattr(extractBlock1, 'Selectors'):
#         all_selectors = []
#         # Try to get selectors - this might vary by ParaView version
#         try:
#             all_selectors = extractBlock1.Selectors
#             print(f"Selectors: {all_selectors}")
#         except:
#             print("Could not access selectors directly")
    
#     # Try multiple selector patterns
#     selector_patterns = [
#         f'/Root/{probe_name}',
#         f'/{probe_name}',
#         f'{probe_name}',
#         '/Root/',
#         '/'
#     ]
    
#     for pattern in selector_patterns:
#         print(f"Trying selector: '{pattern}'")
#         extractBlock1.Selectors = [pattern]
#         UpdatePipeline()
        
#         # Check if we got data
#         data_check = sm.Fetch(extractBlock1)
#         if data_check and data_check.GetNumberOfBlocks() > 0:
#             print(f"? Success with selector: '{pattern}'")
#             break
#         else:
#             print(f"? No data with selector: '{pattern}'")
#     else:
#         print("? No selector worked, trying without selector...")
#         extractBlock1.Selectors = []  # Empty selector might get all data
    
#     # Continue with the rest of your pipeline
#     extractSurface1 = ExtractSurface(registrationName='ExtractSurface1', Input=extractBlock1)
#     UpdatePipeline()
    
#     surfaceNormals1 = SurfaceNormals(registrationName='SurfaceNormals1', Input=extractSurface1)
#     UpdatePipeline()
    
#     cellSize1 = CellSize(registrationName='CellSize1', Input=surfaceNormals1)
#     UpdatePipeline()
    
#     cellDatatoPointData1 = CellDatatoPointData(registrationName='CellDatatoPointData1', Input=cellSize1)
#     cellDatatoPointData1.CellDataArraytoprocess = ['Area']
#     UpdatePipeline()

#     return cellDatatoPointData1

def load_probed_coords(post_path : str, probe_name : str):
    '''
    Loads x, y, z arrays from saved numpy arrays from probe called probe_name
    '''
    x = np.load(file=f'{post_path}/probe_{probe_name}_x.npy')
    y = np.load(file=f'{post_path}/probe_{probe_name}_y.npy')
    z = np.load(file=f'{post_path}/probe_{probe_name}_z.npy')

    return x, y, z

def load_probed_primary_var(probe_name : str, post_path : str):
    '''
    Loads primary variables ro, rovx, rovy, rovz, roe from probe called 
    probe_name.
    '''

    ro = np.load(file=f'{post_path}/probe_{probe_name}_ro.npy')
    rovx = np.load(file=f'{post_path}/probe_{probe_name}_rovx.npy')
    rovy = np.load(file=f'{post_path}/probe_{probe_name}_rovy.npy')
    rovz = np.load(file=f'{post_path}/probe_{probe_name}_rovz.npy')
    roe = np.load(file=f'{post_path}/probe_{probe_name}_roe.npy')

    return ro, rovx, rovy, rovz, roe



def calc_secondary_var(ro, rovx, rovy, rovz, roe):
    '''
    Calculates secondary variables from probed primary variables.
    
    Parameters:
    -----------
        ro, rovx, rovy, rovz, roe : numpy.ndarray
            Primary variables probed and stored as numpy arrays
            Time series data at all nodes probed.
    Returns:
    --------
        mach, pstat : numpy.ndarray
            Same shape as primary variables
    '''
    gamma = 1.4

    mach = ((rovx**2 + rovy**2 + rovz**2) / (gamma * (gamma-1) * (ro * roe - 0.5 * (rovx**2 + rovy**2 + rovz**2))))**0.5

    pstat = (gamma-1) * (roe - 0.5 * (rovx**2 + rovy**2 + rovz**2) / ro)

    return mach, pstat

# def load_probed_var(probe_name : str, var_name : list, post_path : str):
#     '''
#     Loads saved primary variables and coords for a specific probe name
#     '''
#     variables = {}
#     for var in var_name:
#         variables[var] = np.load(f'{post_path}/probe_{probe_name}_{var}.npy')
#         print(f'Shape of {var}: {variables[var].shape}')
    
#     # _, variables['pstat'] = calc_secondary_var(variables['ro'], variables['rovx'], variables['rovy'], variables['rovz'], variables['roe'])

#     return variables

def plot_time_series_data_point(var, var_name, x_arr, y_arr, z_arr, target_coords, normalisation=None):
    '''
    Plot change in a given variable with time at a GIVEN point coordinate.
    E.g. change in static pressure at point on wing LE upper surface with coordinates coords = (x,y,z)
    If normalisation variable required, enter normalisation value

    var, x_arr, y_arr, z_arr are arrays of shape (nt, nn)
    '''

    # Find point in mesh closest to given coord
    x = x_arr[0]; y = y_arr[0]; z = z_arr[0]

    x_sample, y_sample, z_sample = target_coords
    # find index of point closest to given coord
    sample_index = np.argmin((x-x_sample)**2 + (y-y_sample)**2 + (z - z_sample)**2)
    print(f'Target sample coords: {x_sample, y_sample, z_sample}')
    print(f'Sample point in MESH has coords: {x[sample_index], y[sample_index], z[sample_index]}')
    
    # Extract variable time series at given point
    sampled_var = var[:,sample_index]


    # Normalise sampled variable
    if normalisation is not None:
        sampled_var = (sampled_var - sampled_var[0]) / normalisation

    plt.figure(figsize=(12,6))
    plt.plot(sampled_var, label=f'At ({x[sample_index] :.3f}, {y[sample_index] :.3f}, {z[sample_index] :.3f})')
    plt.xlabel('Outer timestep')
    plt.ylabel(f'Change in {var_name}')
    plt.title(f'Variation in {var_name} with time at sampled station')
    plt.legend()
    plt.grid()
    plt.show()


def calc_lift(post_path, probe_name, pv_data, x, y, z, q):
    '''
    Calculate total lift coefficient C_L on the wing and plot vs time
    q: dynamic pressure for normalisation of lift coefficient
    '''
    
    # load required primary variables
    ro, rovx, rovy, rovz, roe = load_probed_primary_var(probe_name=probe_name, post_path=post_path)

    nt, nn = x.shape
    # calc pstat
    _, pstat = calc_secondary_var(ro, rovx, rovy, rovz, roe)
    print(f'pstat shape {pstat.shape}')

    # initialise array to store pressure force on all nodes at each time step
    pressure_force = np.ones((nt,nn,3)) 
    print(f'pressure force array shape: {pressure_force.shape}')

    for t in range(nt):
        # print(pstat[t,:] * pv_data['Area'])
        # pressure force acts normally into surface, so -ve sign
        pressure_force[t,:,:] = np.einsum('i,ij->ij', pstat[t,:]*pv_data['Area'], pv_data['Normals']) 
    
    print('pressure force calculated from probe: force VECTOR')
    print(pressure_force[0])
    print(pressure_force.shape)

    # integrate over wing surface for total lift force VECTOR
    total_lift_force = np.sum(pressure_force, axis=1)
    print(f'Shape of total lift force: {total_lift_force.shape}')
    # Reference area of wing, S = 191.84 m^2
    S = 191.84

    # normalise for total lift coefficient: C_L = L / (1/2ro*v^2*S)
    C_L = np.linalg.norm(total_lift_force, axis=1) / (q * S)
    print(f'shape of total lift coefficient: {C_L.shape}')
    np.save(f'{post_path}/C_L_m0850_q5500_H25_w0_70_alpha_1.npy', C_L)

    print(C_L[:3])

    plt.figure(figsize=(12,6))
    plt.plot(C_L, label='total lift coefficient')
    plt.xlabel('Outer timestep')
    plt.ylabel('$C_L$')
    plt.title('Change in lift with time')
    plt.grid()
    plt.show()

    return C_L

    


def calc_root_BM(post_path, probe_name, pv_data,x, y, z):
    '''
    calculate root BM and plot graph of root BM vs time
    '''
    # load probe data of pstat and rovz and coords

    # x = np.load(file=f'{post_path}/probe_x.npy')
    # y = np.load(file=f'{post_path}/probe_y.npy')
    # z = np.load(file=f'{post_path}/probe_z.npy')
    # pstat = np.load(file=f'{post_path}/probe_pstat.npy')

    ro, rovx, rovy, rovz, roe = load_probed_primary_var(probe_name=probe_name, post_path=post_path)

    # calc pstat
    _, pstat = calc_secondary_var(ro, rovx, rovy, rovz, roe)

    print('probed pstat')
    print(np.max(pstat), np.min(pstat))

    nt, nn = x.shape
    print(f'nt: {nt}')
    print(f'nn: {nn}')

    # print(pstat[0,:] * pv_data['Area'])
    # print(pv_data['pstat'] * pv_data['Area'])


    # initialise array to store pressure force on all nodes at each time step
    pressure_force = np.ones((nt,nn,3)) 
    # define y-ccord of root as the minimum y coord present in array y
    y_root = np.min(y)
    y_prime = np.zeros((nn,3)) # y distance between each node to the root y coord
    y_prime[:,1] = y[0] - y_root

    print('y_prime')
    print(y_prime)
    print(y_prime.shape)
    print(f'Min y_prime = {np.min(y_prime)}. Max y_prime = {np.max(y_prime)}')
    for t in range(nt):
        # print(pstat[t,:] * pv_data['Area'])
        # pressure force acts normally into surface, so -ve sign
        pressure_force[t,:,:] = np.einsum('i,ij->ij', pstat[t,:]*pv_data['Area'], pv_data['Normals']) 
    
    print('pressure force calculated from probe: force VECTOR')
    print(pressure_force[0])
    print(pressure_force.shape)

    # # integrate over wing surface for total lift force VECTOR
    # total_lift_force = np.sum(pressure_force, axis=1)
    # print(f'Shape of total lift force: {total_lift_force.shape}')
    # # Reference area of wing, S = 191.84 m^2
    # S = 191.84

    # # normalise for total lift coefficient: C_L = L / (1/2ro*v^2*S)
    # C_L = np.linalg.norm(total_lift_force, axis=1) / (q * S)
    # if True:
    #     np.save(f'{post_path}/C_L_m0850_q_5500_H25_w0_70.npy', C_L)
    # print(f'shape of total lift coefficient: {C_L.shape}')

    # print(C_L[:3])

    # plt.figure(figsize=(12,6))
    # plt.plot(C_L, label='total lift coefficient')
    # plt.xlabel('Outer timestep')
    # plt.ylabel('$C_L$')
    # plt.title('Change in lift with time')
    # plt.grid()
    # plt.show()



    
    # initialise array to store root bending moment vector at EACH TIME STEP
    bm_root_all_nodes = np.ones((nt,nn,3))
    BM_root = np.ones((nt, 3))
    # calculate total root BM at EACH time step:
    for t in range(nt):
        bm = np.cross(y_prime, pressure_force[t,:,:])
        bm_root_all_nodes[t,:,:] = bm
        BM_root[t,:] = bm.sum(axis=0)
    
    print('root bending moment vector at ALL timesteps')
    print(BM_root)
    print(BM_root.shape)


    # find magnitude of root bending moment at ALL timesteps
    BM_root_mag = np.linalg.norm(BM_root, axis=1)
    bm_root_all_nodes_mag = np.linalg.norm(bm_root_all_nodes,axis=2)
    # print('Root bending moment at all timesteps')
    # print(BM_root_mag)

    # save time delay 
    max_rootBM_time_delay = np.argmax(bm_root_all_nodes_mag, axis=0)
    print(f'shape of max_rootBM_time_delay: {max_rootBM_time_delay.shape}')
    if False:
        np.save(file=f'{post_path}/max_rootBM_time_delay', arr=max_rootBM_time_delay)

    # calculate time difference between root BM peak and rovz peak for each node
    bm_rovz_time_lag = np.argmax(bm_root_all_nodes_mag, axis=0) - np.argmax(rovz, axis=0) 

    print('time lag between bm and rovz peaks for all nodes')
    print(bm_rovz_time_lag[:5])
    print(bm_rovz_time_lag.shape)
    if False:
        np.save(file=f'{post_path}/time_lag_peak_root_bm_rovz', arr=bm_rovz_time_lag)
    
    S = 191.84
    c_mean=7
    normalised_root_BM = -BM_root_mag / (q * S * c_mean)


    if True:
        np.save(f'{post_path}/rootBM_m0850_q5500_H25_w0_70_alpha_1.npy', normalised_root_BM)

    # plot root BM magnitude change normalised by initial root BM
    plt.figure(figsize=(12,6))
    plt.plot(normalised_root_BM, label='Root bending moment')
    plt.xlabel('Outer timestep')
    plt.ylabel('Normalised root bending moment')
    plt.title('Root bending moment vs time in gust encounter')
    plt.grid()
    plt.show()

    return BM_root_mag


if __name__ =='__main__':

    filename = './probe_out.xdmf'
    post_path = './post-processing'
    probe_name_wing = 'wing_surface_pstat'
    probe_name_y = 'y_cut1'
    target_station = (31.24, 10.88, 4.62)
    # dynamic pressure for normalisation
    q=5500

    cellData = calc_cell_props(filename=filename, probe_name=probe_name_wing)

    # load coords probed
    x,y, z = load_probed_coords(post_path=post_path, probe_name=probe_name_wing)
    # extract pressure force data
    pv_data = PVDataToNumpy(data=cellData, points=False)
    print(f'Varaibles available: {pv_data.keys()}')

    # print('pstat')
    # print(pv_data['pstat'])
    # print(pv_data['pstat'].shape)


    print('Cells Normals')
    print(pv_data['Normals'])
    print(pv_data['Normals'].shape)

    print('Cell Area')
    print(pv_data['Area'])
    print(pv_data['Area'].shape)


    BM_root_mag = calc_root_BM(post_path=post_path, probe_name=probe_name_wing,pv_data=pv_data, x=x, y=y, z=z)

    # plot total lift coefficient with time
    C_L = calc_lift(post_path=post_path, probe_name=probe_name_wing, pv_data=pv_data, x=x, y=y, z=z, q=q)
    # probed_vars = load_probed_var(probe_name=probe_name_y,var_name=['pstat'], post_path=post_path)
    
    
    # ==========================================
    # Plot change in pressure at target_station
    # ==========================================
    x2, y2, z2 = load_probed_coords(post_path=post_path, probe_name=probe_name_y)
    ro, rovx, rovy, rovz, roe = load_probed_primary_var(probe_name=probe_name_y, post_path=post_path)
    _, pstat = calc_secondary_var(ro, rovx, rovy, rovz, roe)
    plot_time_series_data_point(var=pstat, var_name='pstat', x_arr=x2, y_arr=y2, z_arr=z2, target_coords=target_station, normalisation=q)





    # print('calculated pstat force')
    # pstat_force = pv_data['pstat'] * pv_data['Normals'] * pv_data['Area']
    # print(pstat_force)
    # print(pstat_force.shape)

    # print('p_force from Kailen code FORCE VECTOR: can only extract time step 0')
    # print(pv_data['p_force'])
    # print(pv_data['p_force'].shape)

    # plt.figure(figsize=(12,6))
    # plt.plot(bm_root_all_nodes_mag[:,0], label='Change in Root bending moment magnitude')
    # plt.xlabel('Outer step')
    # plt.ylabel('Normalised change in root bending moment magnitude')
    # plt.title('Root bending magnitude change in gust encounter')
    # plt.grid()
    # plt.show()
    if False:
        plt.figure(figsize=(12,6))
        plt.plot(max_rootBM_time_delay, label='Time delay in max root BM at each node')
        plt.xlabel('Node index')
        plt.ylabel('Time delay in max root BM at each node')
        # plt.title('Root bending magnitude change in gust encounter')
        plt.grid()
        plt.show()

        # time lag between peak root BM and peak rovz for all nodes
        plt.figure(figsize=(12,6))
        plt.plot(max_rootBM_time_delay[0], label='Time delay in max root BM at each node')
        plt.xlabel('Outer step')
        plt.ylabel('Peak root BM time index - peak rovz time index')
        plt.title('Time lag of peak root BM and rovz for all nodes')
        plt.grid()
        plt.show()







    # print(pv_data['p_force'].shape)

    # print(pv_data['rovz'])


