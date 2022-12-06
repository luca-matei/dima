import sys
from app.modules.utils.utils import utils, no_logs_cmd as cmd

src_dir = utils.get_src_dir()
if len(sys.argv) > 1:
    if sys.argv[1] == "--install":
        modules = (
            "utils/utils.py",
            "logs.py",
            "utils/dbs.py",
            "gpg.py",
            "install.py",
            )
        print("Making install.py ...")
        utils.write(src_dir + "install.py", "")
        for module in modules:
            utils.write(src_dir + "install.py", utils.read(src_dir + "app/modules/" + module) + "\n\n", mode='a')

else:
    modules = (
        "utils/utils.py",
        "hal.py",
        "logs.py",
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
