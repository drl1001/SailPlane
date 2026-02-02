import matplotlib.pyplot as plt
import re

def plot_steady_conv(filename : str):
    # Read the log file
    with open(filename, 'r') as file:
        log_content = file.read()

    # Extract ROVX DELTA values and iteration numbers
    iterations = []
    rovx_delta_values = []

    # Pattern to match RK LOOP NO and ROVX DELTA
    pattern = r'RK LOOP NO:\s+(\d+).*?ROVX DELTA:\s+([\d\.\-eE]+)'
    matches = re.findall(pattern, log_content, re.DOTALL)

    for match in matches:
        iteration = int(match[0])
        rovx_delta = float(match[1])
        iterations.append(iteration)
        rovx_delta_values.append(rovx_delta)

    # Plot the convergence
    plt.figure(figsize=(10, 6))
    plt.semilogy(iterations, rovx_delta_values, 'bo-', linewidth=2, markersize=3)
    plt.xlabel('RK Loop Iteration')
    plt.ylabel('ROVX DELTA')
    plt.title('Convergence of ROVX DELTA')
    plt.grid(True, which="both", ls="-", alpha=0.7)
    plt.tight_layout()
    plt.show()

    # # Print the extracted values
    # print("Iteration\tROVX DELTA")
    # for i, (iter_num, value) in enumerate(zip(iterations, rovx_delta_values)):
    #     print(f"{iter_num}\t\t{value}")

if __name__ == '__main__':
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_empty_mesh/run_2225899/mach_0.700/q_5500/steady/log_2.txt'
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.700/q_5500_alpha_3/steady/log_1.txt'
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/steady/log_2.txt'
    log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_2/steady/log_2.txt'
    
    
    
    plot_steady_conv(filename=log_file)