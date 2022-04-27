import glob
import numpy as np
from IPython import get_ipython
py_files = np.sort(glob.glob('/nsls2/data/fxi-new/shared/config/bluesky/profile_collection/startup/*.py'))
for fn in py_files:
    print(f'loading {fn}')
    get_ipython().run_line_magic("run", f"-i {fn}")

