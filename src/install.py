import sys, os, getpass, inspect, subprocess, string, pprint, ast, json, secrets, re, random
from datetime import datetime

class Utils:
    localhost = "127.0.0.1"
    abc = string.ascii_lowercase

    debian_version = None
    hostname = os.uname()[1]

    hal_dir = "/home/hal/"
    logs_dir = hal_dir + "logs/"
    mnt_dir = hal_dir + "mnt/"
    projects_dir = hal_dir + "projects/"
    res_dir = hal_dir + "res/"
    ssh_dir = hal_dir + "ssh/"
    ssl_dir = hal_dir + "ssl/"
    tmp_dir = hal_dir + "tmp/"
    vms_dir = hal_dir + "vms/"

    dbs = None
    nets = None
    hosts = None
    projects = None
    webs = None
    apps = None
    softs = None

    md2html = None
    yml2html = None

    def __init__(self):
        self.get_debian_version()
        self.src_dir = self.get_src_dir()

    def get_debian_version(self):
        debian_version = self._cmd(None, "cat /etc/debian_version", catch=True).split('.')
        if len(debian_version) < 3:
            debian_version += ['0']

        self.debian_version = '.'.join(debian_version)
        return self.debian_version

    def get_src_dir(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        return file_path.split('src')[0] + 'src/'

    def print_dict(self, d):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(d)

    def get_keys(self, d):
        return list(d.keys())

    def get_values(self, d):
        return list(d.values())

    def reverse_dict(self, d):
        return {y:x for x, y in d.items()}

    def now(self):
        # https://miro.medium.com/max/2138/1*O7E2cZsFohFNj_oGEe-dYg.png
        return datetime.now().strftime("%d %b, %H:%M:%S")

    def read(self, path, lines=False):
        is_ast = path.endswith('.ast')
        is_json = path.endswith('.json')

        with open(path, mode='r', encoding='utf-8') as f:
            if is_ast:
                return ast.literal_eval(f.read())
            elif is_json:
                if f: return json.loads(f)
                else: return ""
            elif lines:
                return f.readlines()
            else:
                return f.read()

    def write(self, path, content, lines=False, mode='w', owner=""):
        # Web apps can't configure themselves
        final_path = None
        if path.startswith("/etc/"):
            final_path = path
            path = utils.tmp_dir + 'tmp_file'

        with open(path, mode=mode, encoding='utf-8') as f:
            if lines:
                f.writelines(content)
            else:
                if path.endswith(".ast"):
                    pprint.pprint(content, stream=f)
                else:
                    f.write(content)

        if final_path:
            cmd(f"sudo mv {path} {final_path}")
            if not owner:
                log(f"No owner specified for '{final_path}'!", level=4, console=True)
            else:
                cmd(f"sudo chown {owner}:{owner} {final_path}")

    def color(self, txt, name):
        colors = {
            'black': (0, 30),
            'red': (0, 31),
            'green': (0, 32),
            'orange': (0, 33),
            'blue': (0, 34),
            'purple': (0, 35),
            'cyan': (0, 36),
            'lgray': (0, 37),
            'dgray': (1, 30),
            'lred': (1, 31),
            'lgreen': (1, 32),
            'yellow': (1, 33),
            'lblue': (1, 34),
            'lpurple': (1, 35),
            'lcyan': (1, 36),
            'white': (1, 37),
            }
        return f"\033[{colors[name][0]};{colors[name][1]}m{txt}\033[0m"

    def new_pass(self, length):
        characters = list(string.ascii_letters + string.digits)
        return ''.join([secrets.choice(characters) for x in range(length)])

    def make_table(self, header, rows):
        rows.insert(0, header)
        table = []
        col_lens = []
        row_sep = ""
        min_spacing = 2

        # For every column in header
        for i, col in enumerate(header):
            # Maximum column length, default set to header
            max_col_len = len(col)

            # Find largest column length for every row
            for row in rows:
                col_len = len(str(row[i]))
                if col_len > max_col_len: max_col_len = col_len
            col_lens.append(max_col_len)

            # Creates row separator
            row_sep += '+' + (max_col_len + min_spacing) * '-'

        row_sep += '+'
        for row in rows:
            table.append(row_sep)
            table_row = ""
            for i, field in enumerate(row):
                field = str(field)
                spaces = (col_lens[i] - len(field) + min_spacing)/2

                if int(spaces) == spaces: odd = 0
                else: odd = 1
                spaces = int(spaces)

                table_row += "|" + spaces*' ' + field + spaces*' ' + odd*' '
            table_row += "|"
            table.append(table_row)
        table.append(row_sep)

        return '\n'.join(table)

    def isfile(self, path, root=False):
        if path.startswith('/etc'): root = True
        if cmd(f"{'sudo ' if root else ''}ls {path}", catch=True):
            return 1
        return 0

    def format_tpl(self, tpl, keys):
        tpl = self.read(self.get_src_dir() + "assets/tpls/" + tpl)

        for key in self.get_keys(keys):
            tpl = tpl.replace("%" + key.upper(), str(keys[key]))

        return tpl

    def yes_no(self, question):
        resp = ""
        yes = "y", "yes", "1",
        no = "n", "no", "0",

        while resp not in yes + no:
            resp = input(f"{question} y(es) / n(o): ")

        if resp in yes: return 1
        elif resp in no: return 0

    def _cmd(self, call_info, command, catch=False):
        output = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output.stdout = output.stdout.strip('\n')
        output.stderr = output.stderr.strip('\n')

        if call_info:
            #logs._log(call_info, f"{hal.user}@{hal.host} {command}")
            logs._log(call_info, output.stdout, level=1)
            if output.stderr: logs._log(call_info, output.stderr, level=4)
        else:
            if output.stderr: print(self.color("Error: ", "lred") + output.stderr)

        if catch:
            response = '\n'.join([output.stdout, output.stderr]).strip('\n')
            #print(response)
            return response

utils = Utils()

def cmd(*args, **kwargs):
    a = inspect.currentframe()
    call_info = inspect.getframeinfo(a.f_back)[:3]
    return utils._cmd(call_info, *args, **kwargs)

def no_logs_cmd(*args, **kwargs):
    return utils._cmd(None, *args, **kwargs)


class Logs:
    # Projects have a cron job to tell Hal to retrieve logs
    # To do: method to change log level
    file_path = __file__.split('/')
    file_dir, file_name = '/'.join(file_path[:-1]) + '/', file_path[-1]

    if file_name == "install.py":
        log_file = file_dir + 'install.log'
    else:
        log_file = utils.logs_dir + utils.get_src_dir().split('/')[-3] + ".log"

    levels = {
        1: ("Debug", "blue"),
        2: ("Info", "green"),
        3: ("Warning", "yellow"),
        4: ("Error", "lred"),
        5: ("Critical", "red"),
        }
    level = 1
    quiet = False

    def _log(self, call_info, message, console=False, level=2):
        # Web apps have console = False

        if level not in range(1, 6):
            self.create_record(call_info, 3, "Log level set incorrectly!")
            level = self.level

        if level >= self.level:
            self.create_record(call_info, level, message)

        if console and not self.quiet:
            print(utils.color(*self.levels[level]) + ": " + message)

        if level == 5:
            print("Exiting ...")
            sys.exit()

    def create_record(self, call_info, level, message):
        filename, lineno, function = call_info
        if function == "execute" and level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{utils.now()} {filename.split('/')[-1]} l{lineno} {function}() {self.levels[level][0]}: {message}\n"

        utils.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        utils.write(self.log_file, "")

logs = Logs()

def log(*args, **kwargs):
    a = inspect.currentframe()
    call_info = inspect.getframeinfo(a.f_back)[:3]
    logs._log(call_info, *args, **kwargs)


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

        if self.opts['has_db']:
            cmd(f"hal {utils.hostname} config postgres")
            print()

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
        packages = "build-essential", "python3", "python3-dev", "python3-venv", "python3-pip", "gnupg2",

        if self.opts['has_web']:
            packages += "openssl", "nginx", "supervisor",

        if self.opts['has_web'] or self.opts['has_db']:
            packages += "postgresql", "libpq-dev",

        if self.opts['has_ssh_server']:
            packages += "openssh-server",

        if self.opts['has_ssh_client']:
            packages += "openssh-client",

        if self.opts['has_vms']:
            # packages +=
            pass

        if self.opts['has_dhcp']:
            packages += "isc-dhcp-server"

        if self.opts['has_dns']:
            packages += "bind9"

        if self.opts['has_firewall']:
            packages += "nftables",

        for package in packages:
            if not "ok installed" in cmd(f"dpkg -s {package} | grep Status", catch=True):
                cmd(f"apt install {package} -y", catch=True)

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

        dir_tree = utils.logs_dir, utils.mnt_dir, utils.projects_dir, utils.res_dir, utils.ssh_dir, utils.ssl_dir, utils.tmp_dir, utils.vms_dir,

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

    def create_env(self):
        if os.path.isdir(f"{utils.projects_dir}venv/"):
            print("There's already a Virtual Env!")
            yes = utils.yes_no("Purge it?")

            if yes: cmd(f"sudo -u hal rm -r {utils.projects_dir}venv/")
            else: return

        print("Creating Virtual Env ...")
        cmd(f"sudo -u hal python3 -m venv {utils.projects_dir}venv")

        packages = "wheel",
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


