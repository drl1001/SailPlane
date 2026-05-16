# Base parameters common to all probes
base = dict(
    nstep_save_start_1d=0,
    nstep_save_1d=1,
    nstep_save_start_2d=0,
    nstep_save_2d=1
)



specs = [


    #Boundarycellprobe to extract pstat on surface of wing.
    dict(name='probe_le',domain=0,
    kind='bcell',
    value={'name':
           'le-wall-wing-whole-wall-freestream'
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_wing_middle',domain=0,
    kind='bcell',
    value={'name': 
        'main-wing-wall-wing-middle-wall-wing-whole-wall-freestream',
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_main_wing',domain=0,
    kind='bcell',
    value={'name': 
        'main-wing-wall-wing-whole-wall-freestream', 
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_root_wing',domain=0,
    kind='bcell',
    value={'name': 
        'root-wing-wall-wing-whole-wall-freestream',   
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_te',domain=0,
    kind='bcell',
    value={'name': 
        'te-wall-wing-whole-wall-freestream', 
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_tip',domain=0,
    kind='bcell',
    value={'name': 
        'tip-wall-wing-whole-wall-freestream',
    },
    aname_list=['ro','rovx','rovy','rovz','roe','x','y','z','twall_x','pstat'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    # #Cartesianplanecut
    # dict(name='probe_y_cut1',domain=0,
    # kind='y',value=10, # starting location of gust
    # aname_list=['ro','rovx','rovy', 'rovz', 'roe','x', 'y', 'z','pstat'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

]