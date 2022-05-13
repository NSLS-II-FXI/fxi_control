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
    func_name = f'fxi_load_{fname_write_short.split(".")[0]}'
    file_lines.append(f'def {func_name}():')
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
    file_lines = convert_initial_digit_to_string(file_lines)
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
    lines.append(space4 * 2 + "'introduction': ''' Description:\n '''")
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
        arg_val = ':'.join(t for t in l.split(':')[1:])
        arg_val = arg_val.strip().replace(',', '')
        #arg_val = l[len(arg_name)+1:].strip().replace(',', '')
        lines_copy[i] = arg_name + ': ' + '"' + arg_val + '",'
    return lines_copy

def convert_initial_digit_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        arg_name = l.split(':')[0]
        arg_val = ':'.join(t for t in l.split(':')[1:])
        arg_val = arg_val.strip().replace(',', '')
        try:
            tmp = eval(arg_val)
        except:
            try:
                if arg_val[0].isdigit():
                    lines_copy[i] = arg_name + ':' + '"' + arg_val + '",'
            except:
                pass
    return lines_copy

def convert_epics_to_string(file_lines):
    lines_copy = file_lines.copy()
    idx = []
    for i, l in enumerate(file_lines):
        if 'Epics' in l or 'prefix' in l:
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


def extract_variable(file_name):
    # get defined variable from .py file
    # exclude variable defined inside "function" and "class"
    msg = ''
    with open(file_name, 'r') as f:
       lines = f.readlines()
    arg_name = []
    arg_command = []
    arg_value = []    
    get_ipython().run_line_magic("run", f"-i {file_name}")
    for i, l in enumerate(lines):
        if len(l)-len(l.lstrip()) > 0: # there are leading spaces
            continue
        t = l.split('=')
        if len(t) == 2:
            try:
                #val = eval(t[1])
                arg_name.append(t[0])
                val = eval(arg_name[0])                
                arg_command.append(t[1].replace('\n', ''))
                arg_value.append(val)
            except:
                msg = f'Syntax error found in line {i}'
                continue
    dict = {}
    n = len(arg_command)
    for i in range(n):
        tmp_dict = {}
        tmp_dict['command'] = arg_command[i].lstrip()
        tmp_dict['value'] = arg_value[i]
        tmp_dict['type'] = 'variable'
        dict[arg_name[i]] = tmp_dict
    return dict


def extract_function(fname, key='def'):
    with open(fname, 'r') as f:
        lines = f.readlines()        
    n = len(lines)
    n_fun = 0
    dict_fun = {}
    txt_fun_name = []
    line_fun = []    
    len_key = len(key)   
    find_fun = False 
    for i in range(n-1):        
        l = lines[i]
        l_next = lines[i+1]
        if l[:len_key+1] == key + ' ':
            find_fun = True
            txt_fun_name.append(l[len_key:].split('(')[0].lstrip())
        if find_fun:
            line_fun.append(l)
            if l_next[0] != ' ':                
                dict_fun[txt_fun_name[-1]] = line_fun
                line_fun = []
                n_fun = n_fun + 1
                find_fun = False
    if find_fun:
        if l_next[0] == ' ':
            line_fun.append(l_next)
        dict_fun[txt_fun_name[-1]] = line_fun
        n_fun += 1 

    dict = {}
    for k in dict_fun.keys():
        tmp_dict = {}
        tmp_dict['command'] = dict_fun[k]
        tmp_dict['value'] = ''
        tmp_dict['type'] = key
        dict[k] = tmp_dict
    return dict
