import numpy as np
import os
import ts_utils.AR_interpolation.process_nastran as nas
import ts_utils.AR_interpolation.H_interpolator as interp
import time

def save_matrices():
    # Extract Nastran coords
    wingbox_bdf_path = "/home/yl924/Desktop/SailPlane/NASTRAN/wing400d.bdf"
    y_root = 2.8
    cwd = os.getcwd()
    out_dir = cwd + "/Matrices/"

    wingbox_nodes = nas.extract_3D_grid(
        bdf_path=wingbox_bdf_path,
        out_name=f'{out_dir}wingbox_grid',
        save_arrays=True,
        xref=True
    )

    wing_nodes, root_nodes = nas.select_root_nodes(wingbox_nodes, y_root=y_root)

    
    np.save(f'{out_dir}wing_nodes', wing_nodes)
    np.save(f'{out_dir}root_nodes', root_nodes)

    print(f'wing nodes shape: {wing_nodes.shape}')
    print(f'root nodes shape: {root_nodes.shape}')
    print(f'overall shape: {wingbox_nodes.shape}')





if __name__ == '__main__':
    start = time.perf_counter()

    SAVE = False
    SAVE_H = True
    cwd = os.getcwd()
    out_dir = cwd + "/Matrices/"


    if SAVE:
        save_matrices()
    else:
        root_nodes = np.load('Matrices/root_nodes.npy')
        wing_nodes = np.load('Matrices/wing_nodes.npy')


        # print(f'Node IDs that are at root (hence ignored): {root_nodes[:,0]}')
        # print(f'Node IDs enclosed by wing surface, hence force and displacement are interpolated onto these: {wing_nodes[:,0]}')

        wing_coords_struct = wing_nodes[:,1:]
        wing_coords_aero = np.load('ts_run/mach_0.720/q_5500/steady/wing_steady_forces/Points.npy')

        span = 28*2
        # build H matrix
        H = interp.create_H(
            x=wing_coords_struct,
            a=wing_coords_aero,
            phi_name='wendland_c2',
            norm_bias=(1., 5., 1.), # norm-bias 5x in spanwise direction to give less weight to points further along span
            r0 = 0.25 * span
        )

        print(f'shape of H: {H.shape}')
        # want condition number to be as close to 1 as possible for well-conditioned matrix
        print(f'Condition number of H: {np.linalg.cond(H)}')

        if SAVE_H:
            np.save(f'{out_dir}H', H)
            print('Saved H matrix')

    end = time.perf_counter()
    print(f'Total runtime: {end - start:.6f} seconds')