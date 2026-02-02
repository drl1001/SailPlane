import os, sys

def slurm_submit_unsteady(nhour: int):
    '''
    Slurm submission script for unsteady runs

    Parameters:
    -----------
    nhour : int
        Hours to run for

    Notes: Default is running on SL2
    '''

    cmd = f'python /home/yl924/Documents/submit_job_a100.py 1 config_3.ofp input_1.hdf5 input_1.hdf5 ../steady/output_2.hdf5 output_3 log_3.txt -nhour {nhour} -qosintr 0 -priority 2'    
    print(f'Running command: {cmd}')
    run = os.system(cmd)

    if run == 0:
        print(f'Successfully submitted slurm job for Unsteady')
    else:
        print(f'Error in submitting slurm job for Unsteady. Command returned exit code: {run}')
        sys.exit(1)

def main():
    print(f'Current working directory: {os.getcwd()}')

    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python slurm_unsteady.py <nhour>")
        print("Example: python slurm_unsteady.py 7")
        sys.exit(1)
    # Run submission script
    slurm_submit_unsteady(nhour=sys.argv[1])


if __name__ == "__main__":
    main()