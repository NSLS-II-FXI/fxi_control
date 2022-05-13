def extract_function(fname, key='def'):
    with open(fname, 'r') as f:
        lines = f.readlines()
        
    n = len(lines)
    n_fun = 0
    txt_fun = {}
    txt_fun_name = []
    line_fun = []
    
    len_key = len(key)
    
    for i in range(n-1):        
        l = lines[i]
        l_next = lines[i+1]
        if l[:len_key+1] == key + ' ':
            find_fun = True
            txt_fun_name.append(l[len_key:].split('(')[0])
        if find_fun:
            line_fun.append(l)
            if l_next[0] != ' ':                
                txt_fun[txt_fun_name[-1]] = line_fun
                line_fun = []
                n_fun = n_fun + 1
                find_fun = False

    if find_fun:
        if l_next[0] == ' ':
            line_fun.append(l_next)
        txt_fun[txt_fun_name[-1]] = line_fun
        n_fun += 1

        
    fsave = 'fun.txt'
    with open(fsave, 'w') as f:
        for k in txt_fun_name:
            f.writelines(txt_fun[k])
            f.writelines('\n')
    return txt_fun
