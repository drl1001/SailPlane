'''
Extracts desired parameter values from given config file path and parameter names.
'''

def extract_param(file_path : str, prefix : str):
    '''
    Extracts values of specified variable names from config files
    '''

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(prefix):

                # for config file parameters which have = signs
                if '=' in line:
                    value = line.split('=')[1]
                    try: 
                        if '.' in value or 'e' in value.lower():
                            value = float(value) # for floats
                        else:
                            value = int(value)
                    except ValueError:
                        value = value

                else: # for log files to read the time step etc.
                    # take whatever comes after the prefix as the number
                    tail = line[len(prefix):].strip()


                    # guard in case the line is incomplete
                    if tail and tail.split()[0].isdigit():
                        value = int(tail.split()[0])
    
    return value


if __name__ == '__main__':
    freq = extract_param(file_path='./uCRM9/ts_ucrm9/run/template_mach/template_point/unsteady/config_3.ofp', prefix='nstep_cycle')
    print(freq)