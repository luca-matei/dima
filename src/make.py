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
        "dima.py",
        "logs.py",
        "task.py",
        "utils/dbs.py",
        "lmobjs/db.py",
        "utils/nets.py",
        "gpg.py",
        "ssh.py",
        "gitlab.py",
        "utils/hosts.py",
        "lmobjs/lmobj.py",
        "lmobjs/net.py",
        "lmobjs/host.py",
        "lmobjs/domain.py",
        "lmobjs/dhcp.py",
        "lmobjs/dns.py",
        "lmobjs/mail.py",
        "utils/projects.py",
        "lmobjs/project.py",
        "utils/webs.py",
        "lmobjs/web.py",
        "utils/apps.py",
        "lmobjs/app.py",
        "utils/softs.py",
        "lmobjs/soft.py",
        "cli.py",
        "gui.py",
        "main.py",
        ),
        module_path = src_dir + "app/modules/",
        file_path = src_dir + "app/app.py")
