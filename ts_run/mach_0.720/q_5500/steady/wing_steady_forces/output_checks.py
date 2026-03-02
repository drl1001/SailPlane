'''
Plot extracted arrays from Paraview to check they make sense. Especially the wing
surface points as previously it was found that the coordinates of surface are
completely wrong.
'''

import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from mpl_toolkits.mplot3d import Axes3D  # needed for 3D plotting

PLOT_aero_mesh = True
SAVE_aero_mesh_plot= True

# if PLOT_aero_mesh:
#     aero_pts = np.load('./ts_run/mach_0.720/q_5500/steady/wing_steady_forces/Points.npy')

#     fig = go.Figure(go.Scatter3d(
#         x=aero_pts[:, 0], y=aero_pts[:, 1], z=aero_pts[:, 2],
#         mode='markers', marker=dict(size=2, opacity=0.5),
#     ))
#     fig.update_layout(title=f'CFD aero surface mesh ({len(aero_pts)} nodes)',
#                       scene=dict(xaxis_title='x [m]', yaxis_title='y [m]', zaxis_title='z [m]'))
#     if SAVE_aero_mesh_plot:
#         fig.write_html('./ts_run/mach_0.720/q_5500/steady/wing_steady_forces/aero_mesh_3D.html')
#         print('Saved aero_mesh_3D.html')
#     fig.show()
def set_axes_equal(ax):
    """
    Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc.
    """
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    x_middle = sum(x_limits) / 2
    y_middle = sum(y_limits) / 2
    z_middle = sum(z_limits) / 2

    plot_radius = 0.5 * max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])

if PLOT_aero_mesh:

    array_dir = './ts_run/mach_0.720/q_5500/steady/wing_steady_forces/'
    # Load CFD aerodynamic surface points
    # aero_pts = np.load('./ts_run/mach_0.720/q_5500/steady/wing_steady_forces/Points.npy')

    # load x, y, z npy arrays
    x = np.load(f'{array_dir}x.npy')
    y = np.load(f'{array_dir}y.npy')
    z = np.load(f'{array_dir}z.npy')


    # Create 3D figure
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Scatter plot
    ax.scatter(x,y,z,
        # aero_pts[:, 0], aero_pts[:, 1], aero_pts[:, 2],
               s=2, alpha=0.5, color='blue')  # s=size, alpha=opacity
    set_axes_equal(ax)

    # Axis labels and title
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_zlabel('z [m]')
    ax.set_title(f'CFD aero surface mesh ({len(x)} nodes)')

    # Optional: save figure as PNG
    if SAVE_aero_mesh_plot:
        plt.savefig('./ts_run/mach_0.720/q_5500/steady/wing_steady_forces/aero_mesh_3D.png', dpi=300)
        print('Saved aero_mesh_3D.png')

    # Show plot
    plt.show()