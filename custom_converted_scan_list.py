def fxi_load_custom_converted_scan_list():
    scan_list = {}
    txm_custom_scan = {
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


    scan_list["txm_custom_scan"] = txm_custom_scan
    return scan_list