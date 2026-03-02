# state file generated using paraview version 5.13.1
# import paraview
# paraview.compatibility.major = 5
# paraview.compatibility.minor = 13

# from paraview.simple import *
# from paraview import servermanager as sm

# import numpy as np
# import vtk
# from vtk.util.numpy_support import vtk_to_numpy

# state file generated using paraview version 5.13.1
import paraview
paraview.compatibility.major = 5
paraview.compatibility.minor = 13

from paraview.simple import *
import numpy as np

# Add the parent directory of ts_utils to Python path
ts_utils_parent = "/rds/project/rds-UemeQPgBLn8/users/yl924"
if ts_utils_parent not in sys.path:
    sys.path.insert(0, ts_utils_parent)

# Import your reusable utilities
from ts_utils.pv_utils.PVDataToNumpy import PVDataToNumpy, SaveSelectedArrays


SAVE_ARRAYS = True 

if __name__ == '__main__':
    # -----------------------------------------------------------------------------
    # Disable automatic camera reset
    # -----------------------------------------------------------------------------
    paraview.simple._DisableFirstRenderCameraReset()

    # -----------------------------------------------------------------------------
    # Pipeline
    # -----------------------------------------------------------------------------

    # TS Reader
    tSTurbostreamReader1 = TSTurbostreamReader(
        registrationName='TSTurbostreamReader1',
        Topologyfilepath='/home/yl924/Desktop/SailPlane/ts_run/mach_0.720/q_5500/steady/input_1.hdf5',
        Valuefilepath='/home/yl924/Desktop/SailPlane/ts_run/mach_0.720/q_5500/steady/output_2.hdf5'
    )

    # Secondary variables
    tSSecondaryVariables1 = TSSecondaryVariables(
        registrationName='TSSecondaryVariables1',
        Input=tSTurbostreamReader1
    )

    # Extract wing wall patches
    extractBlock1 = ExtractBlock(
        registrationName='ExtractBlock1',
        Input=tSSecondaryVariables1
    )

    extractBlock1.Assembly = 'Hierarchy'
    extractBlock1.Selectors = [
        '/Root/BoundaryCells/Domain0/lewallwingwholewallfreestream',
        '/Root/BoundaryCells/Domain0/mainwingwallwingmiddlewallwingwholewallfreestream',
        '/Root/BoundaryCells/Domain0/mainwingwallwingwholewallfreestream',
        '/Root/BoundaryCells/Domain0/rootwingwallwingwholewallfreestream',
        '/Root/BoundaryCells/Domain0/tewallwingwholewallfreestream',
        '/Root/BoundaryCells/Domain0/tipwallwingwholewallfreestream'
    ]

    # Extract surface
    extract_wing_surface = ExtractSurface(
        registrationName='Extract_wing_surface',
        Input=extractBlock1
    )

    # Surface normals
    surfaceNormals1 = SurfaceNormals(
        registrationName='SurfaceNormals1',
        Input=extract_wing_surface
    )
    surfaceNormals1.ComputeCellNormals = 1

    # Cell size (Area)
    cellSize1 = CellSize(
        registrationName='CellSize1',
        Input=surfaceNormals1
    )
    cellSize1.ComputeVertexCount = 0
    cellSize1.ComputeLength = 0
    cellSize1.ComputeVolume = 0

    # Cell data ? point data
    cellDatatoPointData1 = CellDatatoPointData(
        registrationName='CellDatatoPointData1',
        Input=cellSize1
    )

    cellDatatoPointData1.CellDataArraytoprocess = [
        'Area',
        'Normals',
        'pstat'
    ]

    # Calculator
    p_force = Calculator(
        registrationName='p_force',
        Input=cellDatatoPointData1
    )
    p_force.ResultArrayName = 'p_force'
    p_force.Function = 'pstat*Normals*Area'

    # -----------------------------------------------------------------------------
    # Update pipeline
    # -----------------------------------------------------------------------------
    p_force.UpdatePipeline()

    # -----------------------------------------------------------------------------
    # Extract to NumPy
    # -----------------------------------------------------------------------------
    pv_data = PVDataToNumpy(p_force, points=True)

    print("\nFinal extracted arrays:")
    for key in pv_data:
        print(f"{key}: {pv_data[key].shape}")

    # -----------------------------------------------------------------------------
    # Example: compute total pressure force
    # -----------------------------------------------------------------------------
    if "p_force" in pv_data:
        total_force = np.sum(pv_data["p_force"], axis=0)
        print("\nTotal pressure force vector:")
        print(total_force)


# save selected arrays: 
selected_arrays = [
    # 'ro',
    # 'roe',
    # 'rovx',
    # 'rovy',
    # 'rovz',
    # 'p_force',
    # 'Points',
    'x',
    'y',
    'z',
]

if SAVE_ARRAYS:
    SaveSelectedArrays(pv_data,
                    folder_name="wing_steady_forces",
                    array_names=selected_arrays,
                )

#--------------------------------
# OLD 
#--------------------------------
# # -----------------------------------------------------------------------------
# # Utility: Print multiblock structure (for debugging)
# # -----------------------------------------------------------------------------
# def print_structure(block, indent=0):
#     print(" " * indent + block.GetClassName())
#     if block.IsA("vtkMultiBlockDataSet"):
#         for i in range(block.GetNumberOfBlocks()):
#             sub = block.GetBlock(i)
#             if sub:
#                 print_structure(sub, indent + 2)

# # -----------------------------------------------------------------------------
# # Recursive extractor
# # -----------------------------------------------------------------------------
# def extract_from_dataset(dataset, data_arrays, points=False):
#     """
#     Extract arrays from a concrete VTK dataset (vtkPolyData, vtkUnstructuredGrid, etc).
#     """

#     # -----------------------
#     # Point Data
#     # -----------------------
#     pdat = dataset.GetPointData()
#     if pdat:
#         for i in range(pdat.GetNumberOfArrays()):
#             name = pdat.GetArrayName(i)
#             vtk_arr = pdat.GetArray(i)
#             if vtk_arr:
#                 arr = vtk_to_numpy(vtk_arr)
#                 data_arrays.setdefault(name, []).append(arr)
#                 print(f"  Extracted point array: {name} shape={arr.shape}")

#     # -----------------------
#     # Cell Data (optional useful for debugging)
#     # -----------------------
#     cdat = dataset.GetCellData()
#     if cdat:
#         for i in range(cdat.GetNumberOfArrays()):
#             name = cdat.GetArrayName(i)
#             vtk_arr = cdat.GetArray(i)
#             if vtk_arr:
#                 arr = vtk_to_numpy(vtk_arr)
#                 data_arrays.setdefault(name, []).append(arr)
#                 print(f"  Extracted cell array: {name} shape={arr.shape}")

#     # -----------------------
#     # Points
#     # -----------------------
#     if points and dataset.GetPoints():
#         vtk_pts = dataset.GetPoints().GetData()
#         pts = vtk_to_numpy(vtk_pts)
#         data_arrays.setdefault("Points", []).append(pts)
#         print(f"  Extracted Points shape={pts.shape}")


# def traverse_multiblock(block, data_arrays, points=False):
#     """
#     Recursively traverse vtkMultiBlockDataSet until leaf datasets are found.
#     """
#     if block.IsA("vtkMultiBlockDataSet"):
#         for i in range(block.GetNumberOfBlocks()):
#             sub_block = block.GetBlock(i)
#             if sub_block:
#                 traverse_multiblock(sub_block, data_arrays, points)
#     else:
#         extract_from_dataset(block, data_arrays, points)


# def PVDataToNumpy(data, points=False, debug_structure=False):
#     """
#     Convert ParaView pipeline object into dictionary of NumPy arrays.
#     Automatically handles nested MultiBlock datasets.
#     """

#     polydata = sm.Fetch(data)

#     print(f"Extracted data type: {polydata.GetClassName()}")

#     if debug_structure:
#         print("\nDataset structure:")
#         print_structure(polydata)
#         print()

#     data_arrays = {}
#     traverse_multiblock(polydata, data_arrays, points)

#     # Concatenate blocks
#     for key in data_arrays:
#         data_arrays[key] = np.concatenate(data_arrays[key], axis=0)

#     return data_arrays