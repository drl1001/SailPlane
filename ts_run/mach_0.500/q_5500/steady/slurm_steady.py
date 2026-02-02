import os, sys

def slurm_submit_steady(steady: int, nhour: int):
    '''
    Slurm submission script for steady runs

    Parameters:
    -----------
    steady : int
        Steady 1 (laminar) or 2 (turbulent)
    nhour : int
        Hours to run for

    Notes: Default is running on SL2
    '''

    if steady == 1:
        cmd = f'python /home/yl924/Documents/submit_job_a100.py 1 config_1.ofp input_1.hdf5 input_1.hdf5 input_1.hdf5 output_1 log_1.txt -nhour {nhour} -qosintr 0 -priority 2'
    
    elif steady == 2:
        cmd = f'python /home/yl924/Documents/submit_job_a100.py 1 config_2.ofp input_1.hdf5 input_1.hdf5 output_1.hdf5 output_2 log_2.txt -nhour {nhour} -qosintr 0 -priority 2'

    else:
        print('Steady run needs to be 1 or 2, cannot be anything else.')
        sys.exit(1)
    
    print(f'Running command: {cmd}')
    run = os.system(cmd)

    if run == 0:
        print(f'Successfully submitted slurm job for Steady {steady}')
    else:
        print(f'Error in submitting slurm job for Steady {steady}. Command returned exit code: {run}')
        sys.exit(1)

def main():
    print(f'Current working directory: {os.getcwd()}')

    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python slurm_steady.py <1|2> <nhour>")
        print("Example: python slurm_steady.py 2 3")
        sys.exit(1)
    # Run submission script
    slurm_submit_steady(steady=sys.argv[1], nhour=sys.argv[2])


if __name__ == "__main__":
    main()