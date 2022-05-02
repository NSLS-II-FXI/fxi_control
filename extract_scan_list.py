import ast
import numpy as np
from inspect import getmembers, isfunction
import inspect

def prepare_scan_list(fname_read, fname_write='scan_list_test.py'):
    #fname_read = '/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup/41-scans.py'
    source = open(fname_read).read()
    fun = [f.name for f in ast.parse(source).body if isinstance(f, ast.FunctionDef)]
    fun_scan = [f for f in np.sort(fun) if 'scan' in f or 'xanes' in f] # funciton name with "scan"
    
    space4 = ' ' * 4
    file_lines = []
    fname_write_short = fname_write.split('/')[-1]
    file_lines.append(f'def fxi_load_{fname_write_short.split(".")[0]}():')
    file_lines.append(space4 + 'scan_list = {}')
    
    for i in range(len(fun_scan)):
        fun_name = fun_scan[i]
        fun_lines = convert_fun_dict(fun_name)
        for j in range(len(fun_lines)):
            file_lines.append(fun_lines[j])
        file_lines.append('\n')
    
    for i in range(len(fun_scan)):
        fun_name = fun_scan[i]
        file_lines.append(space4 + f'scan_list["txm_{fun_name}"] = txm_{fun_name}')

    file_lines.append(space4 + 'return scan_list')
    file_lines = convert_epics_to_string(file_lines)
    file_lines = convert_fpath_to_string(file_lines)
    with open(fname_write, 'w') as f:
        f.write(f'\n'.join(file_lines))


def convert_fun_dict(fun_name):
    #single_fun = inspect.getfullargspec(eval(fun_name))
    signature = inspect.signature(eval(fun_name))
    '''
    fun_arg = single_fun[0]
    fun_arg_value = single_fun[3]
    '''
    lines = []
    space4 = ' '*4
    
    lines.append(space4 + 'txm_' + fun_name + ' = {')

    for k, v in signature.parameters.items():
        if k == 'md' or k == 'note' or k == 'binning':
            continue
        if v.default is inspect.Parameter.empty:
            if 'detectors' in k or 'eng_list' in k or 'filter' in k:
                val = '[]'
            else:
                val = 'None'
        else:
            val = v.default
        l = f"'{k}': {str(val)}, "
        lines.append(space4 * 2 + l)     
    '''
    for i, arg_name in enumerate(fun_arg):
        
        if arg_name == 'md' or arg_name == 'note' or arg_name == 'binning':
            continue
        l = fun_arg[i] + ': ' + str(fun_arg_value[i]) + ','
        lines.append(space4 * 2 + l)
    '''
    lines.append(space4 * 2 + "'introduction': '''Description:\n '''")
    lines.append(space4 + '}')
    return lines

def convert_fpath_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if '/' in l:
            idx.append(i)
    for i in idx:
        l = file_lines[i]
        arg_name = l.split(':')[0]
        arg_val = l[len(arg_name)+1:].strip().replace(',', '')
        lines_copy[i] = arg_name + ': ' + '"' + arg_val + '",'
    return lines_copy


def convert_epics_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if 'Epics' in l:
            idx.append(i)

    for i in idx:
        l = file_lines[i]
        arg_name = l.split(':')[0]
        lsplit = l.split(',')
        for j, ll in enumerate(lsplit):
            if 'name' in ll:
                break
        arg_val = ll.split('=')[-1]
        lines_copy[i] = arg_name + ': ' + arg_val + ','  
    return lines_copy

    