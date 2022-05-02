import glob
import numpy as np
from IPython import get_ipython
py_files = np.sort(glob.glob('/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup/*.py'))
for fn in py_files:
    print(f'loading {fn}')
    get_ipython().run_line_magic("run", f"-i {fn}")


print('\n\n')
print('#############    Note 1   #################')
print(f'Latest scan_id in this terminal: {RE.md["scan_id"]}')
print(f'Latest scan_id from GUI is:      {db[-1].start["scan_id"]}\n')
print('If two numbers are different, run command: RE.md["scan_id"]=db[-1].start["scan_id"]\n')

print('#############    Note 2   #################')
print('To restart the kernal, run "exit" TWICE !')
#print('###########################################\n')
