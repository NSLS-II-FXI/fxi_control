def fxi_load_scan_list_common():
    scan_list = {}
    txm_aaa_scan = {
        'x_init': None, 
        'introduction': ''' Description:
 '''
    }


    txm_delay_scan = {
        'detectors': [], 
        'motor': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'exposure_time': 0.1, 
        'sleep_time': 1.0, 
        'plot_flag': 0, 
        'simu': False, 
        'mv_back': True, 
        'introduction': ''' Description:
 '''
    }


    txm_eng_scan = {
        'start': None, 
        'stop': None, 
        'num': 1, 
        'detectors': [], 
        'delay_time': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_eng_scan_basic = {
        'start': None, 
        'stop': None, 
        'num': 1, 
        'detectors': 'ic3',
        'delay_time': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_fly_scan = {
        'exposure_time': 0.05, 
        'start_angle': None, 
        'relative_rot_angle': 180, 
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


    txm_fly_scan_repeat = {
        'exposure_time': 0.03, 
        'start_angle': None, 
        'relative_rot_angle': 185, 
        'period': 0.05, 
        'x_list': [], 
        'y_list': [], 
        'z_list': [], 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'rs': 6, 
        'repeat': 1, 
        'sleep_time': 0, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'rot_back_velo': 30, 
        'introduction': ''' Description:
 '''
    }


    txm_fly_scan_test = {
        'exposure_time': 0.05, 
        'start_angle': None, 
        'relative_rot_angle': 180, 
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
        'take_bkg_img': True, 
        'take_dark_img': True, 
        'close_shutter_finish': True, 
        'introduction': ''' Description:
 '''
    }


    txm_multi_pos_xanes_3D = {
        'eng_list': [], 
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'start_angle': None, 
        'exposure_time': 0.05, 
        'relative_rot_angle': 185, 
        'period': 0.05, 
        'out_x': 0, 
        'out_y': 0, 
        'out_z': 0, 
        'out_r': 0, 
        'rs': 2, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'sleep_time': 0, 
        'repeat': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_multipos_2D_xanes_scan = {
        'eng_list': [], 
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'chunk_size': 5, 
        'exposure_time': 0.1, 
        'repeat_num': 1, 
        'sleep_time': 0, 
        'rot_first_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_multipos_2D_xanes_scan2 = {
        'eng_list': [], 
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'exposure_time': 0.2, 
        'sleep_time': 1, 
        'chunk_size': 5, 
        'simu': False, 
        'relative_move_flag': True, 
        'introduction': ''' Description:
 '''
    }


    txm_multipos_2D_xanes_scan3 = {
        'eng_list': [], 
        'x_list': None, 
        'y_list': None, 
        'z_list': None, 
        'r_list': None, 
        'out_x': 0, 
        'out_y': 0, 
        'out_z': 0, 
        'out_r': 0, 
        'repeat_num': 1, 
        'exposure_time': 0.2, 
        'sleep_time': 1, 
        'chunk_size': 5, 
        'simu': False, 
        'relative_move_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_raster_2D_scan = {
        'x_range': [-1, 1], 
        'y_range': [-1, 1], 
        'exposure_time': 0.1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'img_sizeX': 2560, 
        'img_sizeY': 2160, 
        'pxl': 20, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'scan_x_flag': 1, 
        'filters': [], 
        'introduction': ''' Description:
 '''
    }


    txm_raster_2D_scan2 = {
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
        'num_bkg': 1, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'scan_x_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_raster_2D_scan_filter_bkg = {
        'x_range': [-1, 1], 
        'y_range': [-1, 1], 
        'exposure_time': 0.1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'img_sizeX': 2560, 
        'img_sizeY': 2160, 
        'pxl': 20, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'scan_x_flag': 1, 
        'filters': [], 
        'introduction': ''' Description:
 '''
    }


    txm_raster_2D_xanes2 = {
        'eng_list': [], 
        'x_range': [-1, 1], 
        'y_range': [-1, 1], 
        'exposure_time': 0.1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'img_sizeX': 2560, 
        'img_sizeY': 2160, 
        'pxl': 20, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_raster_2D_xanes3 = {
        'eng_list': [], 
        'x_range': [-1, 1], 
        'y_range': [-1, 1], 
        'exposure_time': 0.1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'img_sizeX': 2560, 
        'img_sizeY': 2160, 
        'pxl': 20, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_tomo_mosaic_scan = {
        'x_ini': None, 
        'y_ini': None, 
        'z_ini': None, 
        'x_num_steps': None, 
        'y_num_steps': None, 
        'z_num_steps': None, 
        'x_step_size': None, 
        'y_step_size': None, 
        'z_step_size': None, 
        'exposure_time': 0.05, 
        'period': None, 
        'rs': 4, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'start_angle': None, 
        'relative_rot_angle': 180, 
        'relative_move_flag': True, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_tomo_scan = {
        'start': None, 
        'stop': None, 
        'num': None, 
        'exposure_time': 0.05, 
        'imgs_per_angle': 1, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_xanes_3D = {
        'eng_list': [], 
        'exposure_time': 0.05, 
        'start_angle': None, 
        'relative_rot_angle': 180, 
        'period': 0.06, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'rs': 4, 
        'simu': False, 
        'relative_move_flag': 1, 
        'rot_first_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_xanes_scan = {
        'eng_list': [], 
        'exposure_time': 0.1, 
        'chunk_size': 2, 
        'out_x': 0, 
        'out_y': 0, 
        'out_z': 0, 
        'out_r': 0, 
        'simu': False, 
        'relative_move_flag': 1, 
        'filters': [], 
        'rot_first_flag': 1, 
        'introduction': ''' Description:
 '''
    }


    txm_xanes_scan2 = {
        'eng_list': [], 
        'exposure_time': 0.1, 
        'chunk_size': 5, 
        'out_x': None, 
        'out_y': None, 
        'out_z': None, 
        'out_r': None, 
        'relative_move_flag': 1, 
        'filters': [], 
        'rot_first_flag': 1, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    txm_xanes_scan_img_only = {
        'eng_list': [], 
        'exposure_time': 0.1, 
        'chunk_size': 5, 
        'simu': False, 
        'introduction': ''' Description:
 '''
    }


    scan_list["txm_aaa_scan"] = txm_aaa_scan
    scan_list["txm_delay_scan"] = txm_delay_scan
    scan_list["txm_eng_scan"] = txm_eng_scan
    scan_list["txm_eng_scan_basic"] = txm_eng_scan_basic
    scan_list["txm_fly_scan"] = txm_fly_scan
    scan_list["txm_fly_scan_repeat"] = txm_fly_scan_repeat
    scan_list["txm_fly_scan_test"] = txm_fly_scan_test
    scan_list["txm_multi_pos_xanes_3D"] = txm_multi_pos_xanes_3D
    scan_list["txm_multipos_2D_xanes_scan"] = txm_multipos_2D_xanes_scan
    scan_list["txm_multipos_2D_xanes_scan2"] = txm_multipos_2D_xanes_scan2
    scan_list["txm_multipos_2D_xanes_scan3"] = txm_multipos_2D_xanes_scan3
    scan_list["txm_raster_2D_scan"] = txm_raster_2D_scan
    scan_list["txm_raster_2D_scan2"] = txm_raster_2D_scan2
    scan_list["txm_raster_2D_scan_filter_bkg"] = txm_raster_2D_scan_filter_bkg
    scan_list["txm_raster_2D_xanes2"] = txm_raster_2D_xanes2
    scan_list["txm_raster_2D_xanes3"] = txm_raster_2D_xanes3
    scan_list["txm_tomo_mosaic_scan"] = txm_tomo_mosaic_scan
    scan_list["txm_tomo_scan"] = txm_tomo_scan
    scan_list["txm_xanes_3D"] = txm_xanes_3D
    scan_list["txm_xanes_scan"] = txm_xanes_scan
    scan_list["txm_xanes_scan2"] = txm_xanes_scan2
    scan_list["txm_xanes_scan_img_only"] = txm_xanes_scan_img_only
    return scan_list
