import numpy as np
import paraview.servermanager as sm


def PVDataToNumpy(data, points=False):
    '''
    Function that converts paraview data into a dictionary of numpy arrays for easier subsequent calculation.
 
    parameters:
    -----------
        data: proxy
            paraview object
        points: bool
            True also appends the point coordinate array
 
    returns:
    -----------
        data_arrays: dictionary
            dictionary with keys corresponding to point data arrays. Array data given as numpy arrays.
    '''
    #Fetch data using server manager
    polydata = sm.Fetch(data)
 
    #Get Point Data
    try:
        pdat = polydata.GetPointData()
    except:
        try: 
            block = polydata.GetBlock(0)
            pdat = block.GetRowData()
        except:
            raise NameError('This data type cannot be converted')
    #Iterate over point data to collect array names and arrays
    data_arrays = {}
    n_arr = pdat.GetNumberOfArrays()
    for i in range(n_arr):
        name = pdat.GetArrayName(i)
        arr = np.array(pdat.GetArray(i))
        data_arrays[name] = arr
    #Get point coordinates if required
    if points:
        pts = polydata.GetPoints()
        npoints = pts.GetNumberOfPoints()
        dat = np.zeros((npoints, 3))
        for i in range(npoints):
            dat[i,:] = np.array(pts.GetPoint(i))
        data_arrays["Points"] = dat
 
    return data_arrays


