scan_list = {}

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


scan_list['txm_delay_scan'] = txm_delay_scan
scan_list['txm_delay_count'] = txm_delay_count
scan_list['txm_eng_scan'] = txm_eng_scan
scan_list['txm_z_scan'] = txm_z_scan