from app.modules.utils.utils import utils, no_logs_cmd as cmd

src_dir = utils.get_src_dir()

modules = (
    "utils/utils.py",
    "hal.py",
    "utils/logs.py",
    "utils/dbs.py",
    "db.py",
    "utils/nets.py",
    "net.py",
    "ssh.py",
    "gpg.py",
    "gitlab.py",
    "utils/hosts.py",
    "host.py",
    "utils/projects.py",
    "project.py",
    "utils/webs.py",
    "web.py",
    "utils/apps.py",
    "app.py",
    "utils/softs.py",
    "soft.py",
    "cli.py",
    "utils/yml2html.py",
    "utils/md2html.py",
    "main.py",
    )

print("Making app.py ...")
utils.write(src_dir + "app/app.py", "")
for module in modules:
    utils.write(src_dir + "app/app.py", utils.read(src_dir + "app/modules/" + module) + "\n\n", mode='a')
