import numpy as np
import matplotlib.pyplot as plt

def compare_vars(var_name : str, prop_paths : list, prop_labels : list, prop_mach = None, prop_alpha = None):
    '''
    Plot the same varaible var_name for different conditions prop_labels VS TIME, given their paths (prop_pahts)
    prop_Mach = []: list of Mach numbers if we are comparing the same property at different Mach numbers
    prop_alpha = []: comparing same property at different AOA.
    '''

    props = {}
    plt.figure(figsize=(12,6))

    for i in range(len(prop_paths)):
        prop = np.load(prop_paths[i])
        props[prop_labels[i]] = prop
        if prop_mach is not None:
            # i.e. comparing property different Mach numbers, e.g. CL, root BM coefficient (NON-DIMENSIONAL!)
            # divide by sqrt(1-M^2) to account for compressibility
            plt.plot(prop * np.sqrt(1-prop_mach[i]**2), label=f'{prop_labels[i]}')
            print(f'Mach is {prop_mach[i]}')
        else:
            plt.plot(prop, label=f'{prop_labels[i]}')

    
    # find min timestep to plot
    # times = np.min(props.values(), 
    #                 key=lambda k: props[k].shape[0])
    # print(f'min timesteps {times}')

    
    # for prop in props.values():


    plt.xlabel(f'Time', fontsize=20)
    plt.xticks(fontsize=18)
    plt.ylabel(f'{var_name}',fontsize=20)
    plt.yticks(fontsize=18)
    plt.title(f'Change in {var_name} vs time', fontsize=24)
    plt.legend(fontsize=18, loc='upper right')
    plt.grid()
    plt.show()


def main():
    mach = False
    AoA = True

    if mach:
        # =============================
        # Compare MACH NUMBERS
        # =============================
        # total lift coefficient
        var_name = 'Root Bending Moment'
        prop_paths = [
            '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.700/q_5500/unsteady/post-processing_H25_w0_70/rootBM_m0700_q5500_H25_w0_70.npy',
            '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70.npy'   
        ]

        # var_name = 'Root bending moment'
        # prop_paths = [
        #     '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.700/q_5500/unsteady/post-processing_H25_w0_70/rootBM_m0700_q5500_H25_w0_70.npy',
        #     '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70.npy'
        # ]

        prop_labels = [
            'Mach 0.70',
            'Mach 0.85'
        ]

        prop_mach = [
            0.70,
            0.85
        ]

    if AoA:
        # ==============================
        # COMPARE ANGLE OF ATTACK
        # ==============================
        var_name = 'Root Bending Moment'
        prop_paths = [
            # ROOT BM
            '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70.npy',
            '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_1/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70_alpha_1.npy'

            # CL
            # '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/C_L_m0850_q_5500_H25_w0_70.npy',
            # '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_1/unsteady/post-processing/C_L_m0850_q5500_H25_w0_70_alpha_1.npy'
# 

        ]

        # CL
        #var_name = '$C_L$'
#         prop_paths = [
#             # ROOT BM
#             # '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70.npy',
#             # '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_1/unsteady/post-processing/rootBM_m0850_q5500_H25_w0_70_alpha_1.npy'

#             # CL
#             '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/post-processing/C_L_m0850_q_5500_H25_w0_70.npy',
#             '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_1/unsteady/post-processing/C_L_m0850_q5500_H25_w0_70_alpha_1.npy'
# # 

#         ]


        prop_labels = [
            '$\\alpha = 0^\circ$',
            '$\\alpha = 1^\circ$'
        ]

        prop_mach = [
            0.70,
            0.85
        ]




    compare_vars(var_name=var_name, prop_paths=prop_paths, prop_labels=prop_labels, 
                 )

if __name__ == '__main__':
    main()