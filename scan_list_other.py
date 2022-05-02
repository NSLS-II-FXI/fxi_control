def fxi_load_scan_list_other():
    scan_list = {}
    txm_cond_scan = {
        'detectors': [None], 
        'introduction': ''' Description:
 '''
    }


    txm_knife_edge_scan_for_condensor = {
        'det': [None], 
        'mot1': 'zps_sz',
        'mot1_start': -1000, 
        'mot1_end': 1000, 
        'mot1_points': 11, 
        'mot2': 'zps_sy',
        'mot2_start': -50, 
        'mot2_end': 50, 
        'mot2_points': 11, 
        'mot2_snake': False, 
        'introduction': ''' Description:
 '''
    }


    txm_load_cell_scan = {
        'pzt_cm_bender_pos_list': None, 
        'pbsl_y_pos_list': None, 
        'num': None, 
        'eng_start': None, 
        'eng_end': None, 
        'steps': None, 
        'delay_time': 0.5, 
        'introduction': ''' Description:
 '''
    }


    txm_load_cell_scan_original = {
        'pzt_cm_bender_pos_list': None, 
        'pbsl_y_pos_list': None, 
        'num': None, 
        'eng_start': None, 
        'eng_end': None, 
        'steps': None, 
        'delay_time': 0.5, 
        'introduction': ''' Description:
 '''
    }


    txm_repeat_scan = {
        'detectors': [], 
        'motor': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'num': 1, 
        'sleep_time': 1.2, 
        'introduction': ''' Description:
 '''
    }


    txm_ssa_scan_pbsl_x_gap = {
        'pbsl_x_gap_list': None, 
        'ssa_motor': None, 
        'ssa_start': None, 
        'ssa_end': None, 
        'ssa_steps': None, 
        'introduction': ''' Description:
 '''
    }


    txm_ssa_scan_pbsl_y_gap = {
        'pbsl_y_gap_list': None, 
        'ssa_motor': None, 
        'ssa_start': None, 
        'ssa_end': None, 
        'ssa_steps': None, 
        'introduction': ''' Description:
 '''
    }


    txm_ssa_scan_tm_bender = {
        'bender_pos_list': None, 
        'ssa_motor': None, 
        'ssa_start': None, 
        'ssa_end': None, 
        'ssa_steps': None, 
        'introduction': ''' Description:
 '''
    }


    txm_ssa_scan_tm_yaw = {
        'tm_yaw_pos_list': None, 
        'ssa_motor': None, 
        'ssa_start': None, 
        'ssa_end': None, 
        'ssa_steps': None, 
        'introduction': ''' Description:
 '''
    }


    txm_test_scan = {
        'exposure_time': 0.1, 
        'out_x': -100, 
        'out_y': -100, 
        'out_z': 0, 
        'out_r': 0, 
        'num_img': 10, 
        'num_bkg': 10, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_tm_pitch_scan = {
        'tm_pitch_list': None, 
        'ssa_h_start': None, 
        'ssa_h_end': None, 
        'steps': None, 
        'delay_time': 0.5, 
        'introduction': ''' Description:
 '''
    }


    txm_z_scan = {
        'start': -0.03, 
        'stop': 0.03, 
        'steps': 5, 
        'out_x': -100, 
        'out_y': -100, 
        'chunk_size': 10, 
        'exposure_time': 0.1, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_z_scan2 = {
        'start': -0.03, 
        'stop': 0.03, 
        'steps': 5, 
        'out_x': -100, 
        'out_y': -100, 
        'out_z': 0, 
        'chunk_size': 10, 
        'exposure_time': 0.1, 
        'introduction': ''' Description:
 '''
    }


    txm_z_scan3 = {
        'start': -0.03, 
        'stop': 0.03, 
        'steps': 5, 
        'out_x': -100, 
        'out_y': -100, 
        'chunk_size': 10, 
        'exposure_time': 0.1, 
        'introduction': ''' Description:
 '''
    }


    scan_list["txm_cond_scan"] = txm_cond_scan
    scan_list["txm_knife_edge_scan_for_condensor"] = txm_knife_edge_scan_for_condensor
    scan_list["txm_load_cell_scan"] = txm_load_cell_scan
    scan_list["txm_load_cell_scan_original"] = txm_load_cell_scan_original
    scan_list["txm_repeat_scan"] = txm_repeat_scan
    scan_list["txm_ssa_scan_pbsl_x_gap"] = txm_ssa_scan_pbsl_x_gap
    scan_list["txm_ssa_scan_pbsl_y_gap"] = txm_ssa_scan_pbsl_y_gap
    scan_list["txm_ssa_scan_tm_bender"] = txm_ssa_scan_tm_bender
    scan_list["txm_ssa_scan_tm_yaw"] = txm_ssa_scan_tm_yaw
    scan_list["txm_test_scan"] = txm_test_scan
    scan_list["txm_tm_pitch_scan"] = txm_tm_pitch_scan
    scan_list["txm_z_scan"] = txm_z_scan
    scan_list["txm_z_scan2"] = txm_z_scan2
    scan_list["txm_z_scan3"] = txm_z_scan3
    return scan_list