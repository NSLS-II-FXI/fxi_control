def txm_load_scan_list_common():
    scan_list = {}

    txm_fly_scan = {'exposure_time':0.05,
        'start_angle':0,
        'relative_rot_angle':180,
        'period':0.05,
        'out_x':None,
        'out_y':None,
        'out_z':None,
        'out_r':None,
        'rs':3,
        'relative_move_flag':False,
        'rot_first_flag':True,
        'filters':[],
        'rot_back_velo':30,
        'move_to_ini_pos': True,
        'simu':False,
        'introduction': '''Take tomography in the fly.
        if multiple positions are given, it will repeat the scan at each sample position. '''
    }


    txm_xanes_scan = {
        'eng_list':[],
        'exposure_time':0.05,
        'chunk_size':4,
        'out_x':None,
        'out_y':None,
        'out_z':None,
        'out_r':None,
        'relative_move_flag':False,
        'rot_first_flag':True,
        'filters':[],
        'simu':False,
        'introduction': '''Take XANES image at given energy specified in the energy list. 
        Background image is taken after all XANES images collected. '''
    }


    txm_xanes_scan2 = {
        'eng_list':[],
        'exposure_time':0.05,
        'chunk_size':4,
        'out_x':None,
        'out_y':None,
        'out_z':None,
        'out_r':None,
        'relative_move_flag':False,
        'rot_first_flag':True,
        'filters':[],
        'simu':False,
        'introduction': '''Take XANES image at given energy specified in the energy list. 
        Background image is taken at each energy right after XANES image.'''
    }


    txm_delay_scan = {
        'detectors':[],
        'motor':None,
        'start':None,
        'stop':None,
        'steps':None,
        'exposure_time':0.05,
        'sleep_time':0,
        'plot_flag':True,
        'simu':False,
        'introduction': '''scan a motor and record signals specified in "detectors". 
        If multiple positions are given, it will repeat the scan at each sample position.'''

    }


    txm_delay_count = {
        'detectors':[],
        'num':1,
        'delay':0,
        'plot_flag':True,
        'introduction': 'record signals (images). If plot_flag = True, it will plot the signal after scan.'
    }


    txm_raster_2D_scan = {
        'x_range': [-1, 1],
        'y_range': [-1, 1],
        'exposure_time': 0.1,
        'out_x': 0,
        'out_y': 0,
        'out_z': 0,
        'out_r': 0,
        'img_sizeX': 2560,
        'img_sizeY': 2160,
        'pxl': 17.2,
        'simu': False,
        'relative_move_flag': False,
        'rot_first_flag': 1,
        'scan_x_flag':1,
        'filters': [],
        'introduction': '''raster scan a large area defined by x_range and y_range.
        x_range and y_range indicate the offset of current position with size defined by img_sizeX/Y.
        If multiple positions are given, it will repeat the scan, using the sample position as the center of raster scan.'''
    }


    txm_multipos_2D_xanes_scan2 = {
        'eng_list': [],
        'x_list': [],
        'y_list': [],
        'z_list': [],
        'r_list': [],
        'out_x': None,
        'out_y': None,
        'out_z': None,
        'out_r': None,
        'repeat_num': 1,
        'exposure_time': 0.05,
        'sleep_time': 1,
        'chunk_size': 5,
        'simu': False,
        'relative_move_flag': False,
        'introduction': '''Take xanes spectrum at multiple position.
        Specifically, it will take image and then background at each energy'''
    }


    txm_eng_scan = {
        'start': '',
        'stop': '',
        'num': 1,
        'detectors': [],
        'delay_time': 1,
        'introduction': '''scan the XEng and record signal from (default) [ic3, ic4].
        If "start" is provided as a list, it will omit the setting of "stop" and "num"
        Will plot the intensity curve and differential curve automatically.'''
    }


    txm_raster_2D_xanes = {
        'eng_list': [],
        'x_range': [-1, 1],
        'y_range': [-1, 1],
        'exposure_time': 0.05,
        'out_x': None,
        'out_y': None,
        'out_z': None,
        'out_r': None,
        'img_sizeX': 2560,
        'img_sizeY': 2160,
        'pxl': 20,
        'simu': False,
        'relative_move_flag': False,
        'rot_first_flag': True,
        'introduction': '''Take xanes spectrum at multiple position, defined by "raster 2D scan".
        For each position, it will take image and then background at each energy.'''
    }


    txm_xanes_3D = {
        'eng_list': [],
        'exposure_time': 0.05,
        'start_angle': 0,
        'relative_rot_angle': 180,
        'period': 0.05,
        'chunk_size':20,
        'out_x': None,
        'out_y': None,
        'out_z': None,
        'out_r': None,
        'rs': 2,
        'simu': False,
        'relative_move_flag': False,
        'rot_first_flag': True,
        'introduction': '''Take fly_scan at each energy given by "eng_list".
        If multiple position is given, it will repeat the xanes_3D at each position in sequency'''
    }


    txm_z_scan = {
        'start': -0.03,
        'stop': 0.03,
        'steps': 31,
        'out_x': -100,
        'out_y': 0,
        'chunk_size': 10,
        'exposure_time': 0.05,
        'simu': False,
        'introduction':'''scan the zone-plate to find best focus.
        "out_x", "out_y" are the relative (incremental) movement'''
    }


    scan_list['txm_fly_scan'] = txm_fly_scan
    #scan_list['txm_xanes_scan'] = txm_xanes_scan
    scan_list['txm_xanes_scan2'] = txm_xanes_scan2
    scan_list['txm_multipos_2D_xanes_scan2'] = txm_multipos_2D_xanes_scan2
    scan_list['txm_xanes_3D'] = txm_xanes_3D
    scan_list['txm_raster_2D_xanes'] = txm_raster_2D_xanes
    scan_list['txm_raster_2D_scan'] = txm_raster_2D_scan
    scan_list['txm_delay_scan'] = txm_delay_scan
    scan_list['txm_delay_count'] = txm_delay_count
    scan_list['txm_eng_scan'] = txm_eng_scan
    scan_list['txm_z_scan'] = txm_z_scan

    return scan_list
