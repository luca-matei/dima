from app.modules.utils.utils import utils, no_logs_cmd as cmd

src_dir = utils.get_src_dir()

modules = \
    "utils/utils.py",\
    "hal.py",\
    "utils/logs.py",\
    "utils/dbs.py",\
    "main.py",

print("Making app.py ...")
utils.write(src_dir + "app/app.py", "")
for module in modules:
    utils.write(src_dir + "app/app.py", utils.read(src_dir + "app/modules/" + module) + "\n\n", mode='a')
