import sys
from app.modules.utils.utils import utils, no_logs_cmd as cmd

src_dir = utils.get_src_dir()
if len(sys.argv) > 1:
    if sys.argv[1] == "--install":
        print("Making install.py ...")
        utils.join_modules((
            "utils/utils.py",
            "logs.py",
            "install.py",
            ),
            module_path = src_dir + "app/modules/",
            file_path = src_dir + "install.py")

else:
    print("Making app.py ...")
    utils.join_modules((
        "utils/utils.py",
        "hal.py",
        "logs.py",
        "utils/dbs.py",
        "db.py",
        "utils/nets.py",
        "gpg.py",
        "ssh.py",
        "gitlab.py",
        "utils/hosts.py",
        "lmobj.py",
        "net.py",
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
        "main.py",
        ),
        module_path = src_dir + "app/modules/",
        file_path = src_dir + "app/app.py")
