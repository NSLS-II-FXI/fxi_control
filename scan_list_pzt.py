def fxi_load_scan_list_pzt():
    scan_list = {}
    txm_pzt_energy_scan = {
        'moving_pzt': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'eng_list': [], 
        'detectors': 'dcm_th2',
        'repeat_num': 1, 
        'sleep_time': 1, 
        'fn': "/home/xf18id/Documents/FXI_commision/DCM_scan/",
        'introduction': ''' provide introductory description here '''
    }


    txm_pzt_overnight_scan = {
        'moving_pzt': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'detectors': 'dcm_th2',
        'repeat_num': 10, 
        'sleep_time': 1, 
        'night_sleep_time': 3600, 
        'scan_num': 12, 
        'fn': "/home/xf18id/Documents/FXI_commision/DCM_scan/",
        'introduction': ''' provide introductory description here '''
    }


    txm_pzt_scan = {
        'pzt_motor': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'detectors': 'Vout2',
        'sleep_time': 1, 
        'introduction': ''' provide introductory description here '''
    }


    txm_pzt_scan_multiple = {
        'moving_pzt': None, 
        'start': None, 
        'stop': None, 
        'steps': None, 
        'detectors': 'Vout2',
        'repeat_num': 2, 
        'sleep_time': 1, 
        'fn': "/home/xf18id/Documents/FXI_commision/DCM_scan/",
        'introduction': ''' provide introductory description here '''
    }


    scan_list["txm_pzt_energy_scan"] = txm_pzt_energy_scan
    scan_list["txm_pzt_overnight_scan"] = txm_pzt_overnight_scan
    scan_list["txm_pzt_scan"] = txm_pzt_scan
    scan_list["txm_pzt_scan_multiple"] = txm_pzt_scan_multiple
    return scan_list