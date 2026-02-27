def pvpython_init():
    '''
    Import this function at start of a script to run pvpython and local virtualenv
    together. 
    To execute a script (e.g. my_script.py) that uses both pvpython and libraries in 
    the loca virtualenv, run the following in terminal:

    pvpython my_script.py --virtual-env venv
    '''

    import sys
    if '--virtual-env' in sys.argv:
        virtualEnvPath = sys.argv[sys.argv.index('--virtual-env') + 1]
        virtualEnv = virtualEnvPath + '/bin/activate_this.py'
        exec(open(virtualEnv).read(), {'__file__': virtualEnv})