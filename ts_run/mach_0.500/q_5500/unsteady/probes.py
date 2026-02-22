# Base parameters common to all probes
base = dict(
    nstep_save_start_1d=0,
    nstep_save_1d=1,
    nstep_save_start_2d=0,
    nstep_save_2d=1
)



specs = [
    #Cartesianplanecut
    dict(name='probe_y_cut1',domain=0,
    kind='y',value=12, # starting location of gust
    aname_list=['ro','rovx','rovy', 'rovz', 'roe', 'x', 'y', 'z'],
    mass_avg_aname_list=['hstag'],
    area_avg_aname_list=['pstat'],
    **base),
    
    #Boundarycellprobe to extract pstat on surface of wing.
    dict(name='probe_wingSP_main',domain=0,
    kind='bcell',
    value={'name': 'main-wing-wall'},
    aname_list=['ro','rovx','rovy','rovz','roe', 'twall_x','x','y','z'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_wingSP_le',domain=0,
    kind='bcell',
    value={'name': 'le-wall'},
    aname_list=['ro','rovx','rovy','rovz','roe', 'twall_x','x','y','z'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_wingSP_te',domain=0,
    kind='bcell',
    value={'name': 'te-wall'},
    aname_list=['ro','rovx','rovy','rovz','roe', 'twall_x','x','y','z'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),
    
    dict(name='probe_wingSP_tip',domain=0,
    kind='bcell',
    value={'name': 'tip-wall'},
    aname_list=['ro','rovx','rovy','rovz','roe', 'twall_x','x','y','z'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

    dict(name='probe_wingSP_root',domain=0,
    kind='bcell',
    value={'name': 'root-wing-wall'},
    aname_list=['ro','rovx','rovy','rovz','roe', 'twall_x','x','y','z'],
    mass_avg_aname_list=['hstag','tstag'],
    **base),

]
    # #Cartesianplanecut
    # dict(name='probe_y_cut1',domain=0,
    # kind='y',value=4, # LE of wing root
    # aname_list=['ro','rovz', 'x', 'y', 'z', 'pstat'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),


    # #Cartesianplanecut
    # dict(name='probe_y_cut2',domain=0,
    # kind='y',value=16, # starting location of gust
    # aname_list=['ro','rovx','rovy','rovz', 'roe','x', 'y', 'z'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    # #Cartesianplanecut
    # dict(name='probe_y_cut3',domain=0,
    # kind='y',value=22, # starting location of gust
    # aname_list=['ro','rovx','rovy','rovz', 'roe','x', 'y', 'z'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    # #Cartesianplanecut
    # dict(name='probe_y_cut5',domain=0,
    # kind='y',value=28, # starting location of gust
    # aname_list=['ro','rovx','rovy','rovz', 'x', 'y', 'z', 'pstat'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    #Cartesianplanecut
    # dict(name='probe_x_cut1',domain=0,
    # kind='x',value=-9, # starting location of gust
    # aname_list=['ro','rovx', 'rovy','rovz', 'x', 'y', 'z', 'pstat','mach'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    # #Cartesianplanecut
    # dict(name='probe_x_cut2',domain=0,
    # kind='x',value=31, # LE of halfway along span of wing
    # aname_list=['ro','rovx', 'rovy','rovz', 'x', 'y', 'z', 'pstat','mach'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    # #Cartesianplanecut
    # dict(name='probe_x_cut3',domain=0,
    # kind='x',value=60, # LE of halfway along span of tail
    # aname_list=['ro','rovx', 'rovy','rovz', 'x', 'y', 'z', 'pstat','mach'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

    # #Cartesianplanecut
    # dict(name='probe_x_cut4',domain=0,
    # kind='x',value=90, # Downstream of aircraft if it were there
    # aname_list=['ro','rovx', 'rovy','rovz', 'x', 'y', 'z', 'pstat'],
    # mass_avg_aname_list=['hstag'],
    # area_avg_aname_list=['pstat'],
    # **base),

