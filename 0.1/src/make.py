import os
from app.modules.utils.utils import utils, cmd as utils_cmd

src_dir = os.path.dirname(os.path.abspath(__file__)) + '/'

def cmd(*args, **kwargs):
    return utils_cmd(no_logs=True, *args, **kwargs)

modules = \
    "utils/utils.py",\
    "hal.py",\

print("Making app.py ...")
utils.write(src_dir + "app/app.py", "")
for module in modules:
    utils.write(src_dir + "app/app.py", utils.read(src_dir + "app/modules/" + module) + "\n\n", mode='a')
