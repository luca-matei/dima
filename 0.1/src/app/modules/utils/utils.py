import sys, os, inspect, subprocess, string, pprint, ast, json, secrets
from datetime import datetime

class Utils:
    localhost = "127.0.0.1"
    abc = string.ascii_lowercase

    debian_version = None

    hal_dir = "/home/hal/"
    projects_dir = hal_dir + "projects/"
    ssl_dir = hal_dir + "ssl/"
    vms_dir = hal_dir + "vms/"
    mnt_dir = hal_dir + "mnt/"
    ssh_dir = hal_dir + "ssh/"
    logs_dir = hal_dir + "logs/"
    res_dir = hal_dir + "res/"

    logs = None
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

    def get_debian_version(self):
        debian_version = self._cmd(None, "cat /etc/debian_version", catch=True, no_logs=True).split('.')
        if len(debian_version) < 3:
            debian_version += ['0']

        self.debian_version = '.'.join(debian_version)
        return self.debian_version

    def get_src_dir(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        print(file_path)
        return file_path.split('src/')[0] + 'src/'

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
            path = hal.bay_dir + 'tmp'

        with open(path, mode=mode, encoding='utf-8') as f:
            if lines:
                f.writelines(content)
            else:
                if path.endswith(".ast"):
                    pprint.pprint(content, stream=f)
                else:
                    f.write(content)

        if final_path:
            cmd(f"sudo mv {hal.bay_dir}tmp {final_path}")
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
        tpl = self.read(hal.tpl_dir + tpl)

        for key in self.get_keys(keys):
            tpl = tpl.replace("%" + key.upper(), keys[key])

        return tpl

    def yes_no(self, question):
        resp = ""
        yes = "y", "yes",
        no = "n", "no",

        while resp not in yes + no:
            resp = input(f"{question} y(es) / n(o): ")

        if resp in yes:
            return 1

        elif resp in no:
            return 0

    def _cmd(self, call_info, command, catch=False, no_logs=False):
        output = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output.stdout = output.stdout.strip('\n')
        output.stderr = output.stderr.strip('\n')

        if no_logs:
            if output.stderr: print(self.color("Error: ", "lred") + output.stderr)
        else:
            self.logs._log(call_info, f"{hal.user}@{hal.host} {command}")
            self.logs._log(call_info, output.stdout, level=1)
            if output.stderr: self.logs._log(call_info, output.stderr, level=4)

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
    return utils._cmd(None, no_logs=True, *args, **kwargs)
