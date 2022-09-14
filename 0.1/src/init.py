import sys, os, subprocess, getpass
from app.modules.utils.utils import utils, cmd as utils_cmd

src_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
version = src_dir.split('/')[-3]    # -1 is '', -2 is 'src' and -3 is '0.1'
lmid = "lm1"
help = """
    Help
    """

def cmd(*args, **kwargs):
    return utils_cmd(no_logs=True, *args, **kwargs)

def abort(msg):
    print(f"{msg} Aborting ...")
    sys.exit()

class Init:
    def start(self):
        #self.create_user()
        #self.add_to_group()
        #self.install_dependencies()
        #self.create_sudo()
        self.create_dir_tree()
        self.create_env()
        self.create_cmd()
        self.place_hal()

        cmd(f"sudo -u hal {utils.projects_dir + lmid}/{version}/src/make")

    def create_user(self):
        # https://manpages.debian.org/jessie/adduser/adduser.8.en.html
        if not cmd("getent passwd hal", catch=True):
            print("Creating 'hal' user and group ...")
            cmd("adduser --system --group --no-create-home --disabled-login --gecos '' hal", catch=True)
            cmd(f"echo hal:{utils.new_pass(64)} | chpasswd")
        else:
            print("User 'hal' already exists!")
            yes = utils.yes_no("Use it?")
            if not yes:
                abort("Can't use user 'hal'!")

    def add_to_group(self):
        users = ', '.join([x.split(':')[-1] for x in cmd("getent group hal", catch=True).split('\n')])
        if users:
            print(f"Users already in Hal's group: {users}.")
            yes = utils.yes_no("Add another one?")
            if not yes:
                return

        user = ""
        output = "does not exist"

        while "does not exist" in output:
            user = input("Enter an user to access Hal: ")
            output = cmd(f"usermod -a -G hal {user}", catch=True)

        print(f"{user} has to logout and login again to have access Hal's files!")

    def install_dependencies(self):
        print("Installing dependencies ...")
        packages = "build-essential", "python3", "python3-dev", "python3-venv", "python3-pip", "sudo", "openssl", "postgresql", "libpq-dev", "nginx", "supervisor", "gnupg2", "openssh-client",

        for package in packages:
            if not "ok installed" in cmd(f"dpkg -s {package} | grep Status", catch=True):
                cmd("apt install " + package)

    def create_sudo(self):
        print("Giving sudo permissions to Hal ...")
        cmd_path = "/usr/bin/"
        cmds = "ALL"
        #cmds = "apt",
        #cmds = ', '.join(cmd_path + c for c in cmds)
        cmd(f"echo 'hal ALL=(ALL) NOPASSWD: {cmds}' > /etc/sudoers.d/hal")

    def create_dir_tree(self):
        print("Creating Hal's directory tree ...")

        dir_tree = utils.projects_dir, utils.ssl_dir, utils.vms_dir, utils.mnt_dir, utils.ssh_dir, utils.logs_dir, utils.res_dir,

        if not os.path.isdir(utils.hal_dir):
            cmd(f"mkdir {utils.hal_dir}")

        cmd(f"chown -R hal:hal {utils.hal_dir}")
        cmd(f"chmod g+rwx {utils.hal_dir}")

        for node in dir_tree:
            # It's a directory
            if node.endswith('/') and not os.path.isdir(node):
                cmd(f"sudo -u hal mkdir {node}")

            # It's a file
            elif not os.path.isfile(node):
                cmd(f"sudo -u hal touch {node}")

    def download_resources(self):
        print("Downloading resources ...")
        if not os.path.isfile(f"{utils.res_dir}debian-{utils.debian_version}.iso"):
            print(f"Downloading Debian {utils.debian_version} ...")
            cmd(f"sudo -u hal wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-{utils.debian_version}-amd64-netinst.iso -q -O {utils.res_dir}debian-{utils.debian_version}.iso")
        else:
            print(f"Debian {utils.debian_version} is already installed!")

    def create_env(self):
        if os.path.isdir(f"{utils.projects_dir}venv/"):
            print("There's already a Virtual Env!")
            yes = utils.yes_no("Purge it?")

            if yes:
                cmd(f"rm -r {utils.projects_dir}venv/")
            else:
                return

        print("Creating Virtual Env ...")
        cmd(f"sudo -u hal python3 -m venv {utils.projects_dir}venv")
        cmd(f"sudo -u hal {utils.projects_dir}venv/bin/pip install wheel")
        cmd(f"sudo -u hal {utils.projects_dir}venv/bin/pip install uwsgi psycopg2 libsass pyyaml")

    def create_cmd(self):
        print("Creating 'hal' command ...")
        hal_bash = utils.read(src_dir + "assets/tpls/hal-bash.tpl").replace("%SRC_DIR", src_dir)
        utils.write("/usr/local/bin/hal", hal_bash)
        cmd("chmod +x /usr/local/bin/hal")

    def place_hal(self):
        if os.path.isdir(utils.projects_dir + lmid):
            print(f"Hal already is in the right place!")
            yes = utils.yes_no("Purge it?")
            if yes:
                cmd(f"rm -r {utils.projects_dir + lmid}")
            else:
                return

        print("Placing Hal to its right place ...")
        cmd(f"sudo -u hal git clone https://gitlab.com/lucamatei/{lmid}.git {utils.projects_dir + lmid}/")

args = sys.argv[1:] + ['']
if args[0] in ("-h", "help"):
    print(help)
    sys.exit()

is_root = getpass.getuser() == "root"
if is_root:
    init = Init()
    init.start()
else:
    print("You have to run this script with sudo priviledges!")
