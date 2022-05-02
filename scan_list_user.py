def fxi_load_scan_list_user():
    scan_list = {}
    txm_damon_scan = {
        'eng_list1': [], 
        'eng_list2': [], 
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'exposure_time1': 10.0, 
        'exposure_time2': 10.0, 
        'chunk_size1': 1, 
        'chunk_size2': 1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'iters': 10, 
        'sleep_time': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_dummy_scan = {
        'exposure_time': 0.1, 
        'start_angle': None, 
        'rel_rot_ang': 180, 
        'period': 0.15, 
        'out_x': None, 
        'out_y': 2000, 
        'out_z': None, 
        'out_r': None, 
        'rs': 1, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'filters': [], 
        'rot_back_velo': 30, 
        'repeat': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_fly_scan2 = {
        'exposure_time': 0.05, 
        'start_angle': None, 
        'rel_rot_ang': 180, 
        'period': 0.05, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'rs': 3, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'filters': [], 
        'rot_back_velo': 30, 
        'move_to_ini_pos': True, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_fly_scan3 = {
        'exposure_time': 0.05, 
        'start_angle': None, 
        'rel_rot_ang': 180, 
        'period': 0.05, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'rs': 3, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'filters': [], 
        'rot_back_velo': 30, 
        'move_to_ini_pos': True, 
        'simu': False, 
        'noDark': False, 
        'noFlat': False, 
        'introduction': ''' Description:
 '''
    }


    txm_grid_z_scan = {
        'zstart': -0.03, 
        'zstop': 0.03, 
        'zsteps': 5, 
        'gmesh': [[-5, 0, 5], [-5, 0, 5]], 
        'out_x': -100, 
        'out_y': -100, 
        'chunk_size': 10, 
        'exposure_time': 0.1, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_insitu_xanes_scan = {
        'eng_list': [], 
        'exposure_time': 0.2, 
        'out_x': 0, 
        'out_y': 0, 
        'out_z': 0, 
        'out_r': 0, 
        'repeat_num': 1, 
        'sleep_time': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_ming_scan = {
        'introduction': ''' Description:
 '''
    }


    txm_ming_scan2 = {
        'introduction': ''' Description:
 '''
    }


    txm_ming_scan3 = {
        'introduction': ''' Description:
 '''
    }


    txm_mosaic_fly_scan = {
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'exposure_time': 0.1, 
        'rel_rot_ang': 150, 
        'period': 0.1, 
        'chunk_size': 20, 
        'out_x': None, 
        'out_y': None, 
        'out_z': 4400, 
        'out_r': 90, 
        'rs': 1, 
        'simu': False, 
        'relative_move_flag': 0, 
        'traditional_sequence_flag': 0, 
        'introduction': ''' Description:
 '''
    }


    txm_mosaic_fly_scan_xh = {
        'x_ini': None, 
        'y_ini': None, 
        'z_ini': None, 
        'x_num_steps': 1, 
        'y_num_steps': 1, 
        'z_num_steps': 1, 
        'x_step_size': 0, 
        'y_step_size': 0, 
        'z_step_size': 0, 
        'exposure_time': 0.1, 
        'period': 0.1, 
        'rs': 4, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'start_angle': None, 
        'rel_rot_ang': 180, 
        'relative_move_flag': True, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_qingchao_scan = {
        'eng_list': [], 
        'x_list1': None, 
        'y_list1': None, 
        'z_list1': None, 
        'r_list1': None, 
        'x_list2': None, 
        'y_list2': None, 
        'z_list2': None, 
        'r_list2': None, 
        'sleep_time': 0, 
        'num': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_scan_change_expo_time = {
        'x_range': None, 
        'y_range': None, 
        't1': None, 
        't2': None, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'img_sizeX': 2560, 
        'img_sizeY': 2160, 
        'pxl': 20, 
        'relative_move_flag': 1, 
        'simu': False, 
        'sleep_time': 0, 
        'introduction': ''' Description:
 '''
    }


    txm_tmp_scan = {
        'introduction': ''' Description:
 '''
    }


    txm_user_fly_scan = {
        'exposure_time': 0.1, 
        'rel_rot_ang': 180, 
        'period': 0.15, 
        'chunk_size': 20, 
        'out_x': None, 
        'out_y': 2000, 
        'out_z': None, 
        'out_r': None, 
        'rs': 1, 
        'simu': False, 
        'relative_move_flag': 1, 
        'traditional_sequence_flag': 1, 
        'filters': [], 
        'introduction': ''' Description:
 '''
    }


    txm_user_fly_scan = {
        'exposure_time': 0.1, 
        'rel_rot_ang': 180, 
        'period': 0.15, 
        'chunk_size': 20, 
        'out_x': None, 
        'out_y': 2000, 
        'out_z': None, 
        'out_r': None, 
        'rs': 1, 
        'simu': False, 
        'relative_move_flag': 1, 
        'traditional_sequence_flag': 1, 
        'filters': [], 
        'introduction': ''' Description:
 '''
    }


    txm_user_multiple_fly_scans = {
        'xyz_list': None, 
        'bkg_every_x_scans': 10, 
        'exposure_time': 0.1, 
        'angle': 70, 
        'period': 0.15, 
        'chunk_size': 20, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'rs': 1, 
        'simu': False, 
        'relative_move_flag': 0, 
        'traditional_sequence_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_user_scan = {
        'exposure_time': None, 
        'period': None, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'rs': 1, 
        'out_r': 0, 
        'xanes_flag': False, 
        'xanes_angle': 0, 
        'introduction': ''' Description:
 '''
    }


    txm_xxanes_scan = {
        'eng_list': [], 
        'delay_time': 0.5, 
        'intgr': 1, 
        'dets': 'ic1',
        'repeat': None, 
        'sleep': 1200, 
        'introduction': ''' Description:
 '''
    }


    txm_xxanes_scan2 = {
        'eng_list': [], 
        'dets': 'ic1',
        'repeat': 1, 
        'sleep': 100, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_zps_motor_scan_with_Andor = {
        'motors': None, 
        'starts': None, 
        'ends': None, 
        'num_steps': None, 
        'out_x': 100, 
        'out_y': 0, 
        'out_z': 0, 
        'out_r': 0, 
        'exposure_time': None, 
        'period': None, 
        'chunk_size': 1, 
        'relative_move_flag': 1, 
        'simu': False, 
        'rot_first_flag': 0, 
        'introduction': ''' Description:
 '''
    }


    scan_list["txm_damon_scan"] = txm_damon_scan
    scan_list["txm_dummy_scan"] = txm_dummy_scan
    scan_list["txm_fly_scan2"] = txm_fly_scan2
    scan_list["txm_fly_scan3"] = txm_fly_scan3
    scan_list["txm_grid_z_scan"] = txm_grid_z_scan
    scan_list["txm_insitu_xanes_scan"] = txm_insitu_xanes_scan
    scan_list["txm_ming_scan"] = txm_ming_scan
    scan_list["txm_ming_scan2"] = txm_ming_scan2
    scan_list["txm_ming_scan3"] = txm_ming_scan3
    scan_list["txm_mosaic_fly_scan"] = txm_mosaic_fly_scan
    scan_list["txm_mosaic_fly_scan_xh"] = txm_mosaic_fly_scan_xh
    scan_list["txm_qingchao_scan"] = txm_qingchao_scan
    scan_list["txm_scan_change_expo_time"] = txm_scan_change_expo_time
    scan_list["txm_tmp_scan"] = txm_tmp_scan
    scan_list["txm_user_fly_scan"] = txm_user_fly_scan
    scan_list["txm_user_fly_scan"] = txm_user_fly_scan
    scan_list["txm_user_multiple_fly_scans"] = txm_user_multiple_fly_scans
    scan_list["txm_user_scan"] = txm_user_scan
    scan_list["txm_xxanes_scan"] = txm_xxanes_scan
    scan_list["txm_xxanes_scan2"] = txm_xxanes_scan2
    scan_list["txm_zps_motor_scan_with_Andor"] = txm_zps_motor_scan_with_Andor
    return scan_list