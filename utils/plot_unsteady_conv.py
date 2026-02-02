import re
import matplotlib.pyplot as plt
import numpy as np

def parse_turbostream_log(filename):
    """
    Parse TurboStream log file and extract convergence data for outer steps
    """
    # Patterns to match outer step data
    outer_step_pattern = r'OUTER STEP NO\. (\d+)'
    residual_patterns = {
        'RO': r'RO RESIDUAL: ([\d\.eE+-]+)',
        'ROVX': r'ROVX RESIDUAL: ([\d\.eE+-]+)', 
        'ROVY': r'ROVY RESIDUAL: ([\d\.eE+-]+)',
        'ROVZ': r'ROVZ RESIDUAL: ([\d\.eE+-]+)',
        'ROE': r'ROE RESIDUAL: ([\d\.eE+-]+)',
        'ROVX_DELTA': r'ROVX DELTA:\s+([\d\.eE+-]+)'
    }
    
    # Storage for data
    outer_steps = []
    residuals = {key: [] for key in residual_patterns.keys()}
    
    with open(filename, 'r') as file:
        content = file.read()
    
    # Split content by outer steps
    outer_step_sections = re.split(r'OUTER STEP NO\. \d+', content)
    
    # The first section is before any outer steps, so we skip it
    for i, section in enumerate(outer_step_sections[1:], 1):
        outer_steps.append(i-1)  # Start from step 0
        
        # Extract residuals for this outer step
        for key, pattern in residual_patterns.items():
            match = re.search(pattern, section)
            if match:
                value = float(match.group(1))
                residuals[key].append(value)
            else:
                # If not found, use the previous value or NaN
                if len(residuals[key]) > 0:
                    residuals[key].append(residuals[key][-1])
                else:
                    residuals[key].append(float('nan'))
    
    return outer_steps, residuals

def plot_convergence(outer_steps, residuals, filename=None):
    """
    Plot convergence history for all primary variables
    """
    fig = plt.figure(figsize=(12, 10))
    
    # # Plot residuals on first subplot (log scale)
    # ax1 = axes[0]
    # colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    # for i, (key, values) in enumerate(residuals.items()):
    #     if key != 'ROVX_DELTA':
    #         ax1.semilogy(outer_steps, values, 
    #                     label=key.replace('_', ' '), 
    #                     color=colors[i % len(colors)],
    #                     linewidth=2,
    #                     marker='o' if len(outer_steps) < 50 else '',
    #                     markersize=4)
    
    # ax1.set_xlabel('Outer Step')
    # ax1.set_ylabel('Residual Value (log scale)')
    # ax1.set_title('CFD Convergence History - Primary Variables')
    # ax1.legend()
    # ax1.grid(True, alpha=0.3)
    
    # Plot ROVX_DELTA on second subplot (log scale)
    
    if 'ROVX_DELTA' in residuals and len(residuals['ROVX_DELTA']) > 0:
        plt.semilogy(outer_steps, residuals['ROVX_DELTA'], 
                    label='ROVX DELTA', 
                    color='black',
                    linewidth=2,
                    marker='s' if len(outer_steps) < 50 else '',
                    markersize=4)
    
    plt.xlabel('Outer Step')
    plt.ylabel('ROVX DELTA Value (log scale)')
    plt.title('ROVX DELTA Convergence')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # if filename:
    #     plt.savefig(filename, dpi=300, bbox_inches='tight')
    #     print(f"Plot saved as {filename}")
    
    plt.show()
    
    return fig

def main(log_file):
    # # File path - update this to your actual file path
    # log_file = "./uCRM9/ts_ucrm9/run/mach_0.678/q_5500/unsteady/log_3.txt"
    
    try:
        # Parse the log file
        print("Parsing log file...")
        outer_steps, residuals = parse_turbostream_log(log_file)
        
        # Print some statistics
        print(f"Found {len(outer_steps)} outer steps")
        print("\nResidual ranges:")
        for key, values in residuals.items():
            if values:
                valid_values = [v for v in values if not np.isnan(v)]
                if valid_values:
                    print(f"  {key}: {min(valid_values):.2e} to {max(valid_values):.2e}")
        
        # Plot the convergence
        print("\nGenerating convergence plot...")
        plot_convergence(outer_steps, residuals, "cfd_convergence_plot.png")
        
    except FileNotFoundError:
        print(f"Error: File '{log_file}' not found.")
        print("Please update the 'log_file' variable with the correct path to your log file.")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    # log_file =  '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_empty_mesh/run/mach_0.700/q_5500/unsteady/log_3.txt'
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_empty_mesh/run_2225899/mach_0.700/q_5500/unsteady/log_3.txt'
    # log_file = "/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500/unsteady/log_3.txt"
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_empty_mesh/run_9820595/mach_0.700/q_5500/unsteady/log_3.txt'
    # log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run_H10/mach_0.700/q_5500/unsteady/log_3.txt'
    log_file = '/home/yl924/rds/rds-aeroelasticity-UemeQPgBLn8/users/yl924/uCRM/uCRM9/ts_full_model/run/mach_0.850/q_5500_alpha_1/unsteady/log_3.txt'
    main(log_file=log_file)