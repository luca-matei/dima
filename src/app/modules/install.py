class Install:
    def start(self):
        self.src_dir = utils.get_src_dir()
        self.opts = utils.read(self.src_dir + "install.ast")
        self.lmid = self.opts['lmid']

        self.create_sudo()
        print()
        self.install_deps()
        print()
        self.create_user()
        print()
        self.add_to_group()
        print()
        self.create_dir_tree()
        print()
        self.create_env()
        print()
        self.create_cmd()
        print()

        if self.opts['is_main']:
            self.place_hal()
            print()

        if self.opts['has_db']:
            query = """sudo -u postgres psql -tAc \"{}\""""
            cmd(query.format(f"create role hal with login createdb createrole password '{utils.new_pass(64)}';"))
            cmd(query.format("create database hal owner hal encoding 'utf-8';"))

        cmd(f"sudo -u hal {utils.projects_dir + self.lmid}/make")
        cmd(f"hal {utils.hostname} config git")

        #if self.opts['has_db']:
            #cmd(f"hal {utils.hostname} config postgres")
            #print()

        if self.opts['has_web']:
            cmd(f"hal {utils.hostname} config nginx")
            print()

        cmd(f"chmod -R g+w {utils.hal_dir}")

    def abort(self, msg):
        print(f"{msg} Aborting ...")
        sys.exit()

    def create_sudo(self):
        if not "ok installed" in cmd(f"dpkg -s sudo | grep Status", catch=True):
            print("Installing sudo ...")
            cmd("apt install sudo")

        print("Giving sudo permissions to Hal ...")
        cmd_path = "/usr/bin/"
        cmds = "ALL"
        #cmds = "apt",
        #cmds = ', '.join(cmd_path + c for c in cmds)
        cmd(f"echo 'hal ALL=(ALL) NOPASSWD: {cmds}' > /etc/sudoers.d/hal")

    def install_deps(self):
        print("Installing dependencies ...")
        packages = "build-essential", "python3", "python3-dev", "python3-venv", "python3-pip", "gnupg2", "git", "curl",

        if self.opts['has_web']:
            packages += "openssl", "nginx", "supervisor",

        if self.opts['has_web'] or self.opts['has_db']:
            packages += "postgresql", "libpq-dev",

        if self.opts['has_ssh_server']:
            packages += "openssh-server",

        if self.opts['has_ssh_client']:
            packages += "openssh-client",

        if self.opts['has_vms']:
            packages += "bridge-utils",

        if self.opts['has_dhcp']:
            packages += "isc-dhcp-server",

        if self.opts['has_dns']:
            packages += "bind9",

        if self.opts['has_firewall']:
            packages += "nftables",

        for package in packages:
            if not "ok installed" in cmd(f"dpkg -s {package} | grep Status", catch=True):
                cmd(f"apt install {package} -y", catch=True)

    def create_user(self):
        # https://manpages.debian.org/jessie/adduser/adduser.8.en.html
        if not cmd("getent passwd hal", catch=True):
            print("Creating 'hal' user and group ...")
            cmd("adduser --system --group --gecos '' hal", catch=True)
            cmd(f"echo hal:{utils.new_pass(64)} | chpasswd")
        else:
            print("User 'hal' already exists!")
            yes = utils.yes_no("Use it?")
            if not yes:
                self.abort("Can't use user 'hal'!")

    def add_to_group(self):
        users = ', '.join([x.split(':')[-1] for x in cmd("sudo -u hal getent group hal", catch=True).split('\n')])
        if users:
            print(f"Users already in Hal's group: {users}.")
            yes = utils.yes_no("Add another one?")
            if not yes:
                return

        user = ""
        output = "does not exist"

        while "does not exist" in output:
            user = input("Enter an user to access Hal's files: ")
            output = cmd(f"sudo -u hal usermod -a -G hal {user}", catch=True)

        print(f"{user} has to logout and login again to have access to Hal's files!")

    def create_dir_tree(self):
        print("Creating Hal's directory tree ...")

        dir_tree = utils.logs_dir, utils.mnt_dir, utils.projects_dir, utils.projects_dir + "pids/", utils.res_dir, utils.ssh_dir, utils.ssl_dir, utils.tmp_dir, utils.vms_dir,

        if not os.path.isdir(utils.hal_dir):
            cmd(f"mkdir {utils.hal_dir}")
            cmd(f"chown hal:hal {utils.hal_dir}")

        for node in dir_tree:
            # It's a directory
            if node.endswith('/') and not os.path.isdir(node):
                cmd(f"sudo -u hal mkdir {node}")

            # It's a file
            elif not os.path.isfile(node):
                cmd(f"sudo -u hal touch {node}")

        cmd(f"chown www-data:www-data {utils.projects_dir}pids", host=self.lmid)

    def create_env(self):
        if os.path.isdir(f"{utils.projects_dir}venv/"):
            print("There's already a Virtual Env!")
            yes = utils.yes_no("Purge it?")

            if yes: cmd(f"sudo -u hal rm -r {utils.projects_dir}venv/")
            else: return

        print("Creating Virtual Env ...")
        cmd(f"sudo -u hal python3 -m venv {utils.projects_dir}venv")

        packages = "wheel", "netifaces", "requests",
        if self.opts['has_web']:
            packages += "uwsgi", "libsass", "pyyaml",

        if self.opts['has_web'] or self.opts['has_db']:
            packages += "psycopg2",

        for package in packages:
            cmd(f"sudo -u hal {utils.projects_dir}venv/bin/pip install {package}")

    def create_cmd(self):
        print("Creating 'hal' command ...")
        hal_bash = utils.format_tpl("hal-bash.tpl", {"lmid": self.lmid})
        utils.write("/usr/local/bin/hal", hal_bash)
        cmd("chmod +x /usr/local/bin/hal")

    def place_hal(self):
        # To do: download lm1-versions, lm2, lm2-versions
        if os.path.isdir(utils.projects_dir + self.lmid):
            print(f"Hal already is in the right place!")
            yes = utils.yes_no("Purge it?")
            if yes:
                cmd(f"sudo -u hal rm -r {utils.projects_dir + self.lmid}")
            else:
                return

        print("Placing Hal in the right place ...")
        cmd(f"sudo -u hal git clone https://gitlab.com/lucamatei/{self.lmid}.git {utils.projects_dir + self.lmid}/")

help = """
    Help
    """

args = sys.argv[1:] + ['']
if args[0] in ("-h", "help"):
    print(help)
    sys.exit()

if getpass.getuser() == "root":
    install = Install()
    install.start()
else:
    print("You have to run this script with root priviledges!")
