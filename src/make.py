from app.modules.utils.utils import utils, no_logs_cmd as cmd

src_dir = utils.get_src_dir()

modules = (
    "utils/utils.py",
    "hal.py",
    "utils/logs.py",
    "utils/dbs.py",
    "utils/ssh.py",
    "utils/web.py",
    "db.py",
    "cli.py",
    "main.py",
    )

print("Making app.py ...")
utils.write(src_dir + "app/app.py", "")
for module in modules:
    utils.write(src_dir + "app/app.py", utils.read(src_dir + "app/modules/" + module) + "\n\n", mode='a')
