import sys, os, getpass, inspect, subprocess, string, pprint, ast, json, secrets, re, random, ipaddress
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

    def read(self, path, lines=False, host=None):
        is_ast = path.endswith('.ast')
        is_json = path.endswith('.json')

        if is_ast or is_json:
            with open(path, mode='r', encoding='utf-8') as f:
                if is_ast:
                    return ast.literal_eval(f.read())
                elif is_json:
                    if f: return json.loads(f)
                    else: return ""

        elif lines:
            return [x+'\n' for x in no_logs_cmd(f"cat {path}", catch=True, host=host).split('\n')]

        else:
            return no_logs_cmd(f"cat {path}", catch=True, host=host)

    def write(self, path, content, lines=False, mode='w', owner="root", host=None):
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
            cmd(f"sudo chown {owner}:{owner} {final_path}", host=host)

    def copy(self, src, dest, owner="root", host=None):
        if dest.startswith("/etc/"):
            cmd(f"sudo cp {src} {dest}", host=host)
            cmd(f"sudo chown {owner}:{owner} {dest}", host=host)

        else:
            cmd(f"cp {src} {dest}", host=host)

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

    def isfile(self, path, root=False, host=None):
        if path.startswith('/etc'): root = True
        if "No such file or directory" in cmd(f"{'sudo ' if root else ''}ls {path}", catch=True, host=host):
            return 0
        return 1

    def format_tpl(self, tpl, keys):
        tpl = self.read(self.get_src_dir() + "assets/tpls/" + tpl)

        for key in self.get_keys(keys):
            tpl = tpl.replace("%" + key.upper(), str(keys[key]))

        return tpl

    def yes_no(self, question):
        # To do: implement number of tries (see select_opt())
        resp = ""
        yes = "y", "yes", "1",
        no = "n", "no", "0",

        while resp not in yes + no:
            resp = input(f"{question} y(es) / n(o): ")

        if resp in yes: return 1
        elif resp in no: return 0

    def select_opt(self, opts):
        index = 1
        opts.update({0: "Exit"})
        ordered_opts = sorted(utils.get_keys(opts))
        for opt_id in ordered_opts:
            print(f"{index}. {opts.get(opt_id)}")
            index += 1

        resp = 0
        tries = 0
        while resp not in range(1, len(ordered_opts) + 1) and tries < 3:
            resp = input(f"Select an option from 1-{len(ordered_opts)}: ")
            try: resp = int(resp)
            except: pass
            tries += 1

        if tries < 3:
            return ordered_opts[resp - 1]
        return 0

    def _cmd(self, call_info, command, catch=False, host=None):
        # To do: modify to transfer files via ssh (stp)
        # Executing scripts from host: ssh lm32 'bash -s' < /path/to/host/script.sh
        if host != None and host != hal.host_lmid:
            command = f"ssh {host} '{command}'"

        output = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output.stdout = output.stdout.strip('\n')
        output.stderr = output.stderr.strip('\n')

        if call_info:
            logs._log(call_info, command)
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

class Hal:
    lmid = None
    version = None
    settings = None

    app_dbid = None
    web_dbid = None
    net_dbid = None
    host_dbid = None
    db = None

    app_lmid = "lm1"
    web_lmid = "lm2"
    net_lmid = "lm3"
    host_lmid = "lm4"

    modules = {}

    domain = None
    domains = {}

    lmobjs = {}
    pools = {}

    def status(self):
        print("STATUS")

    def start(self):
        self.app_dir = utils.src_dir + "app/"
        self.tpls_dir = utils.src_dir + "assets/tpls/"

        # Reset logs
        logs.reset()

        log("Phase 1: Checking integrity ...")

        log("Phase 2: Loading modules ...")
        lib_path = utils.projects_dir + "venv/lib/"
        packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
        sys.path.append(packages_path)

        for module in ('psycopg2', 'yaml', 'netifaces', 'requests'):
            globals()[module] = __import__(module)

        log("Phase 3: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        for attr in ("lmid", "version", "domain"):
            setattr(self, attr, settings.get(attr))

        logs.level = settings.get("log_level", 1)
        Gitlab.domain = settings.get("gitlab_domain")
        Gitlab.user = settings.get("gitlab_user")

        log("Phase 4: Loading database ...")
        self.db = Db(self.lmid)
        self.db.erase()
        self.db.build()

        self.load_database()

        log("Phase 5: Checking services ...")
        self.check()
        #ssh.check()

        log("Phase 6: Creating object pools ...")
        for dbid in utils.get_keys(self.lmobjs):
            if isinstance(dbid, int):
                self.create_pool(dbid)

    def load_database(self):
        log("Phase 4.1: Loading modules ...")
        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]   # 1 = utils.dbs
            self.modules[m[1]] = m[0]   # utils.dbs = 1

        log("Phase 4.2: Loading domains ...")
        for d in self.db.execute("select id, name from domains;"):
            self.domains[d[0]] = d[1]
            self.domains[d[1]] = d[0]

        log("Phase 4.3: Loading host environments ...")
        for e in self.db.execute("select id, name from host.envs;"):
            utils.hosts.envs[e[0]] = e[1]
            utils.hosts.envs[e[1]] = e[0]

        log("Phase 4.4: Loading project languages ...")
        for l in self.db.execute("select id, code from project.langs;"):
            utils.projects.langs[l[0]] = l[1]    # 1 = en
            utils.projects.langs[l[1]] = l[0]    # en = 1

        log("Phase 4.5: Loading project themes ...")
        for t in self.db.execute("select id, code from project.themes;"):
            utils.projects.themes[t[0]] = t[1]   # 1 = light
            utils.projects.themes[t[1]] = t[0]   # light = 1

        log("Phase 4.6: Loading web modules ...")
        for m in self.db.execute("select id, name from web.modules;"):
            utils.webs.modules[m[0]] = m[1]    # 1 = static
            utils.webs.modules[m[1]] = m[0]    # static = 1

        log("Phase 4.7: Loading command actions ...")
        for act in hal.db.execute("select id, name, alias from command.acts;"):
            cli.acts[act[0]] = act[1]    # id = name
            cli.acts[act[1]] = act[0]    # name = id
            if act[2]:
                cli.acts[act[2]] = act[0]    # alias = id

        log("Phase 4.8: Loading command objects ...")
        module_ids = []
        for obj in hal.db.execute("select id, module, name, acts, args from command.objs;"):
            module_id = obj[1]
            if module_id not in module_ids:
                cli.objs[module_id] = {}
                module_ids.append(module_id)

            if obj[2] == None: name = ""
            else: name = obj[2]
            cli.objs[module_id][obj[0]] = obj[2:]    # id = name, acts, args
            cli.objs[module_id][name] = obj[0]     # name = id

        log("Phase 4.9: Loading command arguments ...")
        for arg in hal.db.execute("select id, name, act, positional, regex, is_bool, short, long from command.args;"):
            cli.args[arg[0]] = arg[1:]    # id = act, req etc.

        log("Phase 4.10: Loading objects data ...")
        # Load lm objects
        for lmobj in self.db.execute("select id, lmid, module, alias from lmobjs order by id;"):
            self.lmobjs[lmobj[0]] = lmobj[1:]      # 1 = lm1, 10 ('app' module id), astatin
            self.lmobjs[lmobj[1]] = lmobj[0]       # lm1 = 1

            if lmobj[3]:
                self.lmobjs[lmobj[3]] = lmobj[0]   # alias = id

            if lmobj[1] == "lm1": self.app_dbid = lmobj[0]
            elif lmobj[1] == "lm2": self.web_dbid = lmobj[0]
            elif lmobj[1] == "lm3": self.net_dbid = lmobj[0]
            elif lmobj[1] == "lm4": self.host_dbid = lmobj[0]

    def stop(self):
        log("Exiting ...", console=True)
        cli.stop()
        sys.exit()

    def save_settings(self):
        utils.write(self.app_dir + "settings.ast", self.settings)

    def create_pool(self, dbid):
        self.pools[dbid] = getattr(sys.modules[__name__], self.modules[self.lmobjs[dbid][1]])(dbid)
        log(f"Pool {dbid} created.")

    def destroy_pool(self, dbid):
        self.pools.pop(dbid, None)
        log(f"Pool {dbid} destroyed.")

    def insert_lmobj(self, lmid, module, alias):
        log(f"Inserting {lmid} of type {module} ...")
        module_id = hal.modules[module]

        query = f"insert into lmobjs (lmid, module, alias) values (%s, %s, %s) returning id;"
        params = lmid, module_id, alias,
        dbid = hal.db.execute(query, params)[0][0]

        hal.lmobjs[dbid] = list(params)
        hal.lmobjs[lmid] = dbid
        if alias: hal.lmobjs[alias] = dbid

        return dbid

    def next_lmid(self):
        taken = [int(lmid[0][2:]) for lmid in hal.db.execute("select lmid from lmobjs;")]

        for i in range(1, 1000):
            if i not in taken:
                return f"lm{i}"

    def check_alias(self, alias):
        forbidden = "", "q", "exit"

        if alias in forbidden or alias.startswith("lm") or alias in utils.get_keys(cli.acts):
            log("Can't assign this alias!", level=4, console=True)
            return 0

        elif alias in utils.get_keys(self.lmobjs):
            log(f"Alias already in use by {self.lmobjs[self.lmobjs[alias]][0]}!", level=4, console=True)
            return 0

        else:
            return 1

    def check(self):
        """
        iface = netifaces.interfaces()[1]
        addrs = netifaces.ifaddresses(iface)
        net = addrs[netifaces.AF_INET][0]
        ip, netmask, broadcast = net['addr'], net['netmask'], net['broadcast']
        mac = addrs[netifaces.AF_LINK][0]['addr']
        network = ipaddress.ip_network(ip + '/' + netmask, strict=False)
        gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
        """

        reload = False
        # To do: validate registration details

        for d in (self.domain, 'home.' + self.domain):
            domain_id = self.db.execute("select id from domains where name=%s;", (d,))[0][0]

            if not domain_id:
                domain_id = self.db.execute("insert into domains (name) values (%s) returning id;", (d,))[0][0]
                reload = True

        if not self.net_dbid:
            log("Main network not registered!", level=3, console=True)
            self.net_dbid = self.insert_lmobj(self.net_lmid, "Net", None)

            query = "insert into nets (lmobj, dhcp, dns, pm, domain, netmask, gateway, lease_start, lease_end) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = self.net_dbid, None, None, None, domain_id, netmask, gateway, str(network[4]), str(network[-2]),

            self.db.execute(query, params)
            reload = True

        if not self.host_dbid:
            # https://pypi.org/project/netifaces/
            log("Main host not registered!", level=3, console=True)
            self.host_dbid = self.insert_lmobj(self.host_lmid, "Host", utils.hostname)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = self.host_dbid, mac, self.net_dbid, ip, None, utils.hosts.envs["dev"], None, None, None,

            self.db.execute(query, params)
            reload = True

        if not self.app_dbid:
            self.app_dbid = self.insert_lmobj(self.app_lmid, "App", "hal")

            # Register project
            query = "insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = self.app_dbid, self.host_dbid, self.version, None, None, "Hal", None,
            self.db.execute(query, params)

            # Register database
            query = "insert into project.dbs (host, project) values (%s, %s);"
            params = self.host_dbid, self.app_dbid,
            self.db.execute(query, params)

            # Register app
            query = "insert into project.apps (lmobj, port) values (%s, %s);"
            params = self.app_dbid, None,
            self.db.execute(query, params)

            reload = True

        if not self.web_dbid:
            reload = True

        if reload:
            self.load_database()

hal = Hal()

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

class DbUtils:
    query = """sudo -u hal psql -tAc \"{}\""""

    def create_db(self, host=None):
        pass

    def create_pgrole(self, lmid, host=None):
        # https://www.postgresql.org/docs/current/sql-createrole.html
        log(f"Creating '{lmid}' role ...", console=True)
        password = utils.new_pass(64)

        role_query = self.query.format(f"create role {lmid} with login password '{password}';")
        output = cmd(role_query, catch=True)
        if "already exists" in output:
            log(f"'{lmid}' role already exists!", console=True)
            yes = utils.yes_no("Purge it?")

            if yes: cmd(self.query.format(f"drop database {lmid} if exists; drop role {lmid};"))
            else: return

            cmd(role_query)

        if lmid.startswith("lm"):
            details_path = utils.projects_dir + lmid + "/src/app/db/details.ast"
            details = utils.read(details_path)
            details['pass'] = password
            utils.write(details_path, details)
            return password

        else:
            utils.write(utils.tmp_dir + "db_pass.tmp", password)
            log(f"Password stored in {utils.tmp_dir}db_pass.tmp!", console=True)

    def create_pgdb(self, lmid, host=None):
        log(f"Creating {lmid} database ...", console=True)
        db_query = self.query.format(f"create database {lmid} owner {lmid} encoding 'utf-8';")
        output = cmd(db_query, catch=True)
        if "already exists" in output:
            log(f"{lmid} database already exists!", console=True)
            yes = utils.yes_no("Purge it?")

            if yes: cmd(self.query.format(f"drop database {lmid};"))
            else: return

            cmd(db_query, catch=True)

utils.dbs = DbUtils()

class Db:
    def __init__(self, lmid, dbid=None, host_dbid=None):
        self.lmid = lmid
        self.dbid = dbid
        self.host_dbid = host_dbid
        self.connect()

        # Check if database is empty
        if not self.execute("select count(*) from pg_catalog.pg_tables where schemaname not in ('information_schema', 'pg_catalog');")[0][0]:
            self.build()

    def connect(self):
        def try2connect():
            # To do: get passwords securely
            details = utils.read(utils.src_dir + "app/db/details.ast")
            host = details['host']
            port = details['port']
            password = details['pass']

            self.conn = psycopg2.connect(f"dbname={self.lmid} user={self.lmid} host={host} password={password} port={port}")

        try:
            try2connect()
        except:
            # Maybe PostgreSQL port has updated in the meantime
            #requests.get(f"https://hal.lucamatei.net/c/{self.lmid}/update/db")
            try:
                try2connect()
            except:
                log(f"Cannot connect to {self.lmid} database!", level=5, console=True)

        log(self.lmid + " database connected.")

    def erase(self):
        log(f"Erasing {self.lmid} database ...", console=True)

        # Drop all user created schemas
        schemas = [x[0] for x in self.execute("select s.nspname as table_schema, s.oid as schema_id, u.usename as owner from pg_catalog.pg_namespace s join pg_catalog.pg_user u on u.usesysid = s.nspowner where nspname not in ('information_schema', 'pg_catalog', 'public') and nspname not like 'pg_toast%%' and nspname not like 'pg_temp_%%' order by table_schema;")]
        for schema in schemas:
            self.execute(f"drop schema if exists {schema} cascade;")

        # Drop all remaining user created tables
        tables = [x[0] for x in self.execute("select table_name from information_schema.tables where table_schema='public';")]
        for table in tables:
            self.execute(f"drop table if exists {table} cascade;")

    def build(self):
        log(f"Building {self.lmid} database ...", console=True)
        if self.dbid:
            if self.lmid[2] == 'w':
                struct = utils.read(hal.tpl_dir + "web/app/db/struct.ast")
                default_file = hal.tpl_dir + "web/app/db/default.ast"
        else:
            struct = utils.read(hal.app_dir + "db/struct.ast")
            default_file = hal.app_dir + "db/default.ast"

        for group in struct:
            # Check if the group is a schema
            # group[0] is the schema name / public table name
            # group[1] is the list of tables / of rows
            # group[1][0] is the first table / first row
            if isinstance(group[1][0], tuple):
                self.execute(f"create schema {group[0]};")
                for table in group[1]:
                    self.execute(f"create table {group[0]}.{table[0]} ({','.join(table[1])});")

            # The group is a table
            else:
                self.execute(f"create table {group[0]} ({','.join(group[1])});")

        self.load(default_file)

    def load(self, file):
        # Web apps load data differently bcs they have .html files
        """
        INSERT into scratch (name, rep_id, term_id)
        SELECT 'aaa'
                , r.id
                , t.id
        FROM reps r , terms t -- essentially a cross join
        WHERE r.rep = 'Dracula'
          AND t.terms = 'prepaid';

        Special first row for translating columns from a table
        """

        db_data = utils.read(file)
        for schema in db_data:
            for table in schema[1]:
                struct_row = ', '.join(table[1][0])    # Db structure row
                nmsps = []
                nmsp_tables = []
                nmsp_table_i = 0    # Letter for the namespace table; nets a, guests b etc.
                has_nmsps = False

                for nmsp in table[1][1]:    # Column namespaces row
                    if nmsp:
                        has_nmsps = True
                        nmsp_list = nmsp.split(':')    # translated column, column to translate, table

                        # Lists of namespaces will be treated differently later
                        if not nmsp_list[0].endswith('[]'):
                            nmsp_tables.append(nmsp_list[2] + ' ' + utils.abc[nmsp_table_i])
                            nmsp_list[2] = utils.abc[nmsp_table_i]    # Replace table name with letter
                            nmsp_table_i += 1    # Move forward in the alphabet
                        else:
                            nmsp_list[0] = nmsp_list[0][:-2]    # Remove '[]'

                        nmsps.append(nmsp_list)
                    else:
                        nmsps.append('')

                # To do: validate data
                if has_nmsps:
                    nmsp_tables = ', '.join(nmsp_tables)
                    for row in table[1][2:]:    # Data rows
                        new_row = []
                        wheres = []    # where clause in query

                        for i, col in enumerate(row):
                            if nmsps[i]:
                                # Check if it's a list of namespaces
                                if isinstance(col, tuple):
                                    if col:
                                        query = f"select {nmsps[i][0]} from {nmsps[i][2]} where {nmsps[i][1]} in %s;"
                                        params = col,
                                        values = [x[0] for x in self.execute(query, params)]
                                        sql_list = []

                                        for value in values:
                                            if isinstance(value, str):
                                                if value:
                                                    sql_list.append(f"'{value}'")
                                                else:
                                                    sql_list.append("null")
                                            else:
                                                sql_list.append(str(value))

                                        new_row.append("'{" + ', '.join(sql_list) + "}'")
                                    else:
                                        new_row.append("'{}'")
                                else:
                                    new_row.append(nmsps[i][2] + '.' + nmsps[i][0])                 # Table name . Translated column
                                    wheres.append(nmsps[i][2] + '.' + nmsps[i][1] + f"='{col}'")    # Table name . Column to translate

                            # Column doesn't have a namespace
                            else:
                                if isinstance(col, str):
                                    if col:
                                        new_row.append(f"'{col}'")
                                    else:
                                        new_row.append("null")
                                else:
                                    new_row.append(str(col))

                        new_row = ', '.join(new_row)
                        wheres = ' and '.join(wheres)

                        self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) select {new_row} from {nmsp_tables} where {wheres};")
                else:
                    rows = []
                    ss = []
                    for row in table[1][2:]:
                        rows.extend([None if not value and isinstance(value, str) else value for value in row])
                        ss.append(f"({', '.join(['%s' for x in row])})")
                    ss = ', '.join(ss)

                    self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) values {ss};", rows)

    def export(self, file_path=""):
        if not file_path: file_path = f"/home/hal/tmp/{self.lmid}.db.ast"
        log(f"Exported {self.lmid} database to {file_path}", console=True)

    def execute(self, query, params=()):
        data = ()
        for tries in range(2):
            try:
                cursor = self.conn.cursor()
                break
            except:
                cursor = None

        if cursor == None:
            log("No database cursor!", level=5, console=True)
        else:
            log(f"Query: {query}")
            if params: log(f"Params: {params}")

            try:
                cursor.execute(query, params)
                if query.startswith("select") or "returning" in query:
                    data = cursor.fetchall()
                    log(f"Data: {data}")

            except (Exception, psycopg2.Error) as e:
                # Hitting 'restart postgres will terminate active connections'
                if "server closed the connection" in str(e):
                    self.connect()
                    return self.execute(query, params)

                log(f"Query error: {e}", level=4)
                log(f"Database error!", level=5, console=True)

            self.conn.commit()
            cursor.close()
        return data

    def disconnect(self):
        self.conn.close()
        log(self.lmid + " database disconnected.")

class NetUtils:
    def in_subnets(self):
        subnets = []

        for x in cmd("ip a", catch=True).split(' '):
           if x.startswith(('192.168.', '172.16.', '10.')) and '/' in x:
               subnets.append(x)

        return subnets

    def get_free_ip(self, net_id):
        # This is not bound to a Net because I'll need a free ip on specific nets

        # Get machine's ips
        query = "select ip from host.hosts where net=%s;"
        params = net_id,
        used_ips = hal.db.execute(query, params)

        if used_ips:
            used_ips = [ipaddress.ip_address(ip[0]) for ip in used_ips]

        query = "select netmask, gateway, lease_start, lease_end from nets where lmobj=%s;"
        netmask, gateway, lease_start, lease_end = hal.db.execute(query, params)[0]

        net = ipaddress.ip_network(gateway + '/' + netmask, strict=False)
        lease_start = ipaddress.ip_address(lease_start)
        lease_end = ipaddress.ip_address(lease_end)

        for ip in net.hosts():
            if ip >= lease_start and ip <= lease_end and ip not in used_ips:
                return str(ip)

        log(f"No free ips for net {hal.pools.get(net_id).name}!", level=4, console=True)
        return None

utils.nets = NetUtils()

class GPG:
    def create_gpg_key(self, email):
        log(f"Generating GPG key for '{email}'. This may take a while ...", console=True)

        key_config = utils.format_tpl("gpg-key.tpl", {
            "user": email.split('@')[0],
            "email": email
            })
        utils.write(utils.tmp_dir + "gpg", key_config)

        cmd(f"gpg2 --batch --gen-key {utils.tmp_dir}gpg")

        return self.get_privkey_id(email)

    def get_privkey_id(self, email):
        privkey_id = cmd(f"gpg2 --list-secret-keys --keyid-format LONG {email}", catch=True)
        if not "No secret key" in privkey_id:
            return re.findall(r'\bsec   rsa4096/\w+', privkey_id)[0].split('/')[1]
        else:
            log(f"Couldn't find GPG key for '{email}'!", level=4, console=True)
            yes = utils.yes_no("Create one?")
            if yes:
                return self.create_gpg_key(email)
            return 0

    def delete_gpg_key(self, host):
        cmd(f"gpg2 --batch --delete-secret-keys {email}")
        cmd(f"gpg2 --batch --delete-keys {email}")

gpg = GPG()

class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

    def __init__(self, host_dbid, host_lmid):
        self.host_dbid = host_dbid
        self.host_lmid = host_lmid
        self.email = f"{host_lmid}@{self.domain}"

    def request(self, method="get", endpoint="", data={}):
        method = method.lower()
        if method not in ("get", "post", "delete"):
            log(f"Invalid method '{method}'!", level=4)
            return 0

        headers = {'private-token': self.get_token()}
        url = f"https://{self.domain}/api/v4{endpoint}"

        response = getattr(requests, method)(
            url,
            headers = headers,
            json = data
            )

        return response.json()

    def clone(self, lmid):
        log(f"Cloning {lmid} Gitlab repository ...")
        cmd(f"git clone git@{self.domain}:{self.user}/{lmid}.git {utils.projects_dir}{lmid}/", host=self.host_lmid)

    def add_ssh_key(self):
        if hal.pools.get(self.host_dbid).create_ssh_key(gitlab=True):
            data = {
                'title': self.host_lmid,
                'key': utils.read(utils.ssh_dir + self.host_lmid + "-gitlab.pub", host=self.host_lmid)
                }

            self.request(
                    method = "post",
                    endpoint = "/user/keys",
                    data = data
                    )

    def delete_ssh_key(self):
        hal.pools.get(self.host_dbid).delete_ssh_key(gitlab=True)
        self.request(
            method = "delete",
            endpoint = "/user/keys/" + self.get_ssh_keys(self.host_lmid).get('id')
            )

    def get_ssh_key(self):
        key = None
        for k in self.request(endpoint = "/user/keys"):
            if k.get("title") == self.host_lmid:
                key = k
                break
        return key

    def get_gpg_keys(self):
        keys = self.request(endpoint = "/user/gpg_keys")
        return keys

    def add_email(self):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': self.email}
            )

    def add_gpg_key(self):
        privkey_id = gpg.create_gpg_key(self.email)

        if privkey_id:
            pubkey = cmd("gpg2 --armor --export " + privkey_id, catch=True)

            self.add_email()
            self.request (
                method = "post",
                endpoint = "/user/gpg_keys",
                data =  {'key': pubkey}
                )

            cmd("git config --global user.signingkey " + privkey_id)

    def get_projects(self, lmid=None):
        projects = self.request(endpoint = "/projects")

        if lmid:
            project = None
            for p in projects:
                if p.get("path") == lmid:
                    project = p
                    break
            return project

        return projects

    def create_project(self, data):
        self.request(
            method = "post",
            endpoint = "/projects",
            data = data
        )

    def config_git(self):
        log(f"Configuring Git for {self.host_lmid} ...", console=True)
        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.host_lmid,
            "email": self.email,
            "gpg_key": gpg.get_privkey_id(self.host_lmid)
            })
        utils.write(f"/home/hal/.gitconfig", config, host=self.host_lmid)

    def get_token(self):
        token_file = utils.projects_dir + 'gitlab_token.txt'

        if not utils.isfile(token_file, host=self.host_lmid):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token.")

            token = getpass.getpass("Token: ")
            utils.write(token_file, token, host=self.host_lmid)
            cmd("chmod 600 " + token_file, host=self.host_lmid)

            return token
        else:
            return utils.read(token_file, host=self.host_lmid)

    def check(self):
        if not utils.isfile("/home/hal/.gitconfig"):
            self.config_git()

        if not gitlab.get_ssh_keys(self.lmid):
            gitlab.add_ssh_key(self.lmid)

        if not gitlab.get_gpg_keys():
            gitlab.add_gpg_key(self.lmid)

        if not utils.ssh_dir + self.lmid + "-gitlab" in utils.read("/home/hal/.ssh/config"):
            self.config_ssh_client()

class HostUtils:
    envs = {}

    def preseed_host(self, hostname, net_id, ip):
        arch = "amd" # "386"
        iso_dir = f"{utils.tmp_dir}debian-{utils.debian_version}/"
        print(iso_dir)
        iso_file = f"{hal.src_dir}assets/debian-{utils.debian_version}.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"
        tmp_iso = utils.tmp_dir + hostname + ".iso"

        if os.path.isfile(tmp_iso):
            log(f"Removing {tmp_iso}", level=3)
            cmd(f"sudo rm {tmp_iso}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null")

        log("Creating preseed file ...")
        # utils.new_pass(64)
        net = hal.pools.get(net_id)
        preseed_config = utils.format_tpl("preseed.tpl", {
            "ip": ip,
            "netmask": net.netmask,
            "gateway": net.gateway,
            "dns": hal.pools.get(net.dns_id).ip,
            "hostname": hostname,
            "domain_name": net.domain,
            "root_pass": "test",
            "root_pass_hash": "",
            "user_fullname": "hal",
            "username": "hal",
            "user_pass": "test",
            "user_pass_hash": ""
            })

        utils.write(preseed_file, preseed_config)

        log("Configuring boot options ...")
        utils.write(isolinux_file, '\n'.join([
            "path",
            "label lminstall",
            "    menu label ^Automated LM Install",
            "    kernel /install.amd/vmlinuz",
            "    append auto=true priority=critical vga=788 file=/cdrom/preseed.cfg initrd=/install.amd/initrd.gz --- quiet",
            "default lminstall",
            "prompt 0",
            "timeout 1",
            ]))

        """
        # Adding the preseed file to the Initrd
        log("Adding preseed file ...")
        cmd(f"chmod +w {iso_dir}install.{arch}/")
        cmd(f"gunzip {iso_dir}install.{arch}/initrd.gz")
        cmd(f"echo {preseed_dir}preseed.cfg | cpio -H newc -o -A -F {iso_dir}install.{arch}/initrd")
        cmd(f"gzip {iso_dir}install.{arch}/initrd")
        cmd(f"chmod -w -R {iso_dir}install.{arch}/")
        """

        # Regenerating md5sum.txt
        log("Regenerating md5sum ...")
        cmd(f"chmod +w {iso_dir}md5sum.txt")
        cmd(f"md5sum `find {iso_dir} -follow -type f` > {iso_dir}md5sum.txt")

        md5sum = utils.read(iso_dir + "md5sum.txt")
        md5sum = md5sum.replace(iso_dir, "./")
        utils.write(iso_dir + "md5sum.txt", md5sum)

        cmd(f"chmod -w {iso_dir}md5sum.txt")

        log(f"Creating {lmid}.iso ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {tmp_iso} {iso_dir[:-1]}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir)

        log(f"Preseeded ISO image for {hostname} stored at {self.tmp_iso}", console=True)

    def register_host(self, mode=None):
        # This host can only be a PM
        opts = {
            1: "Create ISO image",
            2: "Create install script",
            }

        lmid = hal.next_lmid()
        alias = None

        while alias != "":
            alias = input("Preferred hostname (Press Enter to skip): ")
            if hal.check_alias(alias):
                break

        hostname = alias if alias else lmid

        mode = utils.select_opt(opts)

        if mode == 1:
            ip = utils.nets.get_free_ip(hal.net_dbid)
            self.preseed_host(hostname, hal.net_dbid, ip)

        elif mode == 2:
            pass

utils.hosts = HostUtils()

class lmObj:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]
        self.alias = hal.lmobjs[dbid][2]
        self.name = self.alias if self.alias else self.lmid

    def set_alias(self, alias):
        if hal.check_alias(alias):
            hal.lmobjs.pop(self.alias, None)
            hal.lmobjs[alias] = self.dbid
            self.alias = alias

            hal.db.execute("update lmobjs set alias=%s where id=%s;", (alias, self.dbid,))
            log(f"Alias '{alias}' set to {self.lmid}.", console=True)

    def delete_alias(self):
        hal.lmobjs.pop(self.alias, None)
        self.alias = None
        hal.db.execute("update lmobjs set alias=%s where id=%s;", (None, self.dbid,))
        log("Alias deleted.", console=True)

class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, dhcp, dns, domain, gateway, lease_start, lease_end from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.dhcp_id, self.dns_id, self.domain_id, self.gateway, self.lease_start, self.lease_end = hal.db.execute(query, params)[0]

        self.domain = hal.domains.get(self.domain_id)

        self.check()

    def set_dhcp(self, host=None):
        def get_opt(opts, db_opts):
            for host in db_opts:
                # Display alias too
                if host[2]:
                    opts[host[0]] = f"{host[1]} ({host[2]})"
                else:
                    opts[host[0]] = host[1]

            return utils.select_opt(opts)

        opts = {
            -2: "Register a host",
            -1: "Create a VM",
            }

        query = "select id, lmid, alias from lmobjs where module=%s;"
        params = hal.modules.get("Host"),
        dhcp_id = get_opt(opts, hal.db.execute(query, params))

        # Register a host
        if dhcp_id == -2:
            utils.hosts.register_host()
            log("You have to run again this command after you've installed the new host!", level=3, console=True)
            return

        # Create a VM
        elif dhcp_id == -1:
            # Select physical machines to host the VM
            query = "select a.id, a.lmid, a.alias from lmobjs a, host.hosts b where b.lmobj=a.id and b.pm=null;"
            pm_id = get_opt({}, hal.db.execute(query))

            if pm_id:
                hal.pools.get(pm_id).create_host()
                self.set_dhcp()
                return
            else:
                log(f"Couldn't create a DHCP server for net {self.name}!", level=4, console=True)

        elif dhcp_id:
            pool = hal.pools.get(dhcp_id)
            if not pool:
                hal.create_pool(dhcp_id)
                pool = hal.pools.get(dhcp_id)

            pool.config_dhcp()
            log(f"{pool.name} set as DHCP server for net {self.name}.", console=True)

        else:
            log(f"Couldn't set a DHCP server for net {self.name}!", level=4, console=True)

    def set_dns(self, host=None):
        pass

    def check(self):
        if not self.dhcp_id:
            log(f"Net {self.name} doesn't have a DHCP server set!", level=3, console=True)
            self.set_dhcp()

        if not self.dns_id:
            log(f"Net {self.name} doesn't have a DNS set!", level=3, console=True)
            self.set_dns()

class HostServices:
    def manage_service(self, action, service):
        log(f"Restarting {service} for {self.name} ...", console=True)
        cmd(f"sudo systemctl {action} {service} ", host=self.lmid)

    def status_service(self, service):
        out = cmd(f"sudo systemctl status {service}", catch=True)
        if "active (running)" in out:
            log(f"{service} is active.", console=True)
            return 1

        elif "failed" in out:
            log(f"{service} failed!", level=4, console=True)
            return 0

    # Nets
    def config_dhcp(self):
        log(f"Configuring DHCP server on {self.name} ...", console=True)
        query = "select a.lmid, b.lmobj, b.dns, b.domain, b.netmask, b.gateway, b.lease_start, b.lease_end from lmobjs a, nets b where a.id = b.lmobj and pm=%s;"
        params = self.dbid,
        nets = hal.db.execute(query, params)

        if not nets:
            log("There are no networks managed by this host!", level=4, console=True)
            return

        for net in nets:
            net_obj = ipaddress.ip_network(net[5] + "/" + net[4], strict=False)
            subnet = str(net_obj).split('/')[0]
            broadcast = str(net_obj[-1])

            if net[1] == hal.net_dbid:
                # Main config
                dhcp_config = utils.format_tpl("dhcp/dhcpd.tpl", {
                    "domain": self.domain,
                    "dns": "8.8.8.8" #self.dns
                    })
                utils.write('/etc/dhcp/dhcpd.conf', dhcp_config, host=self.lmid)

                # default file
                iface = [x for x in cmd("ls /sys/class/net", catch=True, host=self.lmid).split(' ') if x.startswith(("eth", "eno", "enp"))][0]
                init_config = utils.format_tpl("dhcp/default.tpl", {
                    "interfaces": iface,
                    })
                utils.write("/etc/default/isc-dhcp-server", init_config, host=self.lmid)

                # Create subnets and hosts directory
                if not utils.isfile("/etc/dhcp/dhcp.d/", host=self.lmid):
                    cmd("sudo mkdir /etc/dhcp/dhcp.d/", host=self.lmid)

                # Write subnets file
                subnet_config = utils.format_tpl("dhcp/subnet.tpl", {
                    "subnet": subnet,
                    "netmask": net[4],
                    "gateway": net[5],
                    "broadcast": broadcast,
                    "lease_start": net[6],
                    "lease_end": net[7]
                    })
                utils.write("/etc/dhcp/dhcp.d/subnets.conf", subnets_config, host=self.lmid)

                # Write hosts file
                query = "select a.lmid, b.mac, b.ip from lmobjs a, host.hosts b where a.id=b.lmobj and a.net=%s;"
                params = net[1],
                hosts = hal.db.execute(query, params)

                hosts_config = ""
                for host in hosts:
                    host_config = utils.format_tpl("dhcp/host.tpl", {
                        "lmid": host[0],
                        "mac": host[1],
                        "ip": host[2]
                        })

                    hosts_config += host_config + '\n\n'
                utils.write('/etc/dhcp/dhcp.d/hosts.conf', hosts_config, host=self.lmid)

                self.restart_dhcp()

            else:
                query = "select a.lmid, b.mac, b.ip from lmobjs a, host.hosts b where a.id=b.lmobj and a.net=%s;"
                params = net[1],
                hosts = hal.db.execute(query, params)

                hosts_config = '\n'.join([f'<host mac="{host[1]}" ip="{host[2]}"/>' for host in hosts])

                net_xml = utils.format_tpl("dhcp/net.tpl", {
                    "lmid": net[0],
                    "netmask": net[4],
                    "gateway": net[5],
                    "hosts": hosts_config
                    })

    def config_dns(self):
        pass

    def restart_dhcp(self):
        self.manage_service("restart", "isc-dhcp-server")

    def status_dhcp(self):
        self.status_service("isc-dhcp-server")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for {self.name} ...")
        utils.copy(hal.tpls_dir + "web/nginx.tpl", "/etc/nginx/nginx.conf", host=self.lmid)
        self.manage_service("restart", "nginx")

    def reload_nginx(self):
        self.manage_service("reload", "nginx")

    def start_nginx(self):
        self.manage_service("start", "nginx")

    def stop_nginx(self):
        self.manage_service("stop", "nginx")

    def restart_nginx(self):
        self.manage_service("restart", "nginx")

    def status_nginx(self):
        self.status_service("nginx")

    # Postgres
    def config_postgres(self):
        """
        :public
        Manages /etc/postgresql/13/main/postgresql.conf
                /etc/postgresql/13/main/pg_hba.conf
        Assigns a new port to the PostgreSQL server.
        """

        log(f"Configuring PostgreSQL for {self.name} ...", console=True)
        port = self.next_port()

        pg_dir = f"/etc/postgresql/{os.listdir('/etc/postgresql/')[-1]}/main/"
        config_file = pg_dir + "postgresql.conf"

        # Create backup for default configs
        for cfg_file in (config_file, pg_dir + "pg_hba.conf"):
            if not utils.isfile(cfg_file + ".bak", host=self.lmid):
                utils.copy(cfg_file, cfg_file + ".bak", owner="postgres", host=self.lmid)

        # Modify port in config file
        config = utils.format_tpl("pg/postgresql.tpl", {
            "port": port
            })

        # Write new config file and restart service
        utils.write(config_file, config, owner="postgres", host=self.lmid)
        utils.copy(hal.tpls_dir + "pg/pg_hba.tpl", pg_dir + "pg_hba.conf", owner="postgres", host=self.lmid)

        # Update ports in Hal projects and in db
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))

        if self.dbid == hal.host_dbid:
            details_path = hal.app_dir + "db/details.ast"
            details = utils.read(details_path, host=self.lmid)
            details["port"] = port
            utils.write(details_path, details, host=self.lmid)

        self.pg_port = port
        self.manage_service("restart", "postgresql")

    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    def start_postgres(self):
        self.manage_service("start", "postgresql")

    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    def status_postgres(self):
        self.status_service("postgres")

    # Supervisor
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    def status_supervisor(self):
        self.status_service("supervisor")

    # SSH
    def config_ssh_client(self):
        if not utils.isfile("/home/hal/.ssh/", host=self.lmid):
            cmd("mkdir /home/hal/.ssh/", host=self.lmid)

        log(f"Configuring SSH client for {self.name} ...", console=True)
        hosts = ""

        if self.dbid == hal.host_dbid:
            query = "select a.lmid, a.alias, b.ip, b.ssh_port from lmobjs a, host.hosts b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,

            for host in hal.db.execute(query, params):
                hosts += utils.format_tpl("ssh/host.tpl", {
                    "lmid": host[0],
                    "ip": host[2],
                    "port": host[3],
                    "user": "hal",
                    "privkey": utils.ssh_dir + host[0],
                    })

                if host[1]:
                    hosts += utils.format_tpl("ssh/host.tpl", {
                        "lmid": host[1],
                        "ip": host[2],
                        "port": host[3],
                        "user": "hal",
                        "privkey": utils.ssh_dir + host[0],
                    })

        hosts += utils.format_tpl("ssh/host.tpl", {
            "lmid": self.gitlab.domain,
            "ip": self.gitlab.domain,
            "port": 22,
            "user": "git",
            "privkey": utils.ssh_dir + self.lmid + "-gitlab",
            })

        utils.write("/home/hal/.ssh/config", utils.format_tpl("ssh/client_config.tpl", {
            "hosts": hosts,
        }), host=self.lmid)

    def config_ssh_server(self):
        log(f"Configuring SSH server for {self.name} ...", console=True)
        port = self.next_port()

        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))

        if self.dbid != hal.host_dbid:
            config = utils.format_tpl("ssh/server_config.tpl", {
                "port": port,
                })

            utils.write("/etc/ssh/sshd_config", config, host=self.lmid)

        self.config_ssh_client()

    def create_ssh_key(self, gitlab=False):
        log(f"Generating SSH key to access {'Gitlab from ' if gitlab else ''}host '{self.name}'. This may take a while ...", console=True)

        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if gitlab else '')
        cmd(f'ssh-keygen -b 4096 -t ed25519 -a 100 -f {privkey} -q -N ""', host=self.lmid)

        if utils.isfile(privkey):
            cmd("chmod 600 " + privkey, host=self.lmid)
            cmd("chmod 600 " + privkey + ".pub", host=self.lmid)
            self.config_ssh_client()

            return 1
        else:
            log(f"Couldn't generate SSH key to access {'Gitlab from ' if gitlab else ''}host '{self.name}'!", level=4, console=True)

            return 0

    def delete_ssh_key(self, gitlab=False):
        log(f"Removing {'Gitlab ' if gitlab else ''}SSH key for host '{self.name}' ...", console=True)

        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if gitlab else '')
        cmd(f"rm {privkey} {privkey}.pub", host=self.lmid)

        self.config_ssh_client()


class Host(lmObj, HostServices):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select mac, net, ip, client, env, ssh_port, pg_port from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.net_id, self.ip, self.client_id, self.env, self.ssh_port, self.pg_port = hal.db.execute(query, params)[0]

        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.gitlab = Gitlab(self.dbid, self.lmid)

        self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.port, b.port from web.webs a, project.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def has_storage(self, capacity):
        return True

    # Projects
    def create_project(self, lmid, module, name, description, alias, host):
        host_dbid = hal.lmobjs.get(host, 0)
        if isinstance(hal.pools[host_dbid], Host):
            if hal.pools[host_dbid].env == utils.hosts.envs.get("dev"):
                if hal.pools[host_dbid].has_storage("10mb"):
                    gitlab.create_project(data={
                        'path': lmid,
                        'name': name,
                        'description': description,
                        'visibility': 'private',
                        'initialize_with_readme': True,
                        })
                else:
                    log(f"Not enough storage on {host}!", level=4, console=True)
                    return 0
            else:
                log(f"{host} is not a dev machine!", level=4, console=True)
                return 0
        else:
            log(f"{host} is not a host!", level=4, console=True)
            return 0

        if gitlab.get_projects(lmid):
            dbid = hal.insert_lmobj(lmid, module, alias)

            query = f"insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = dbid, host_dbid, 0.1, None, None, name, description,
            hal.db.execute(query, params)

            gitlab.clone(lmid)
            return dbid

        log(f"Couldn't create project {lmid}!", level=4, console=True)
        return 0

    # Web
    def create_web(self, name, description, alias, host, domain, modules, langs, themes, default_lang, default_theme, has_top, has_animations, has_domain_in_title):
        lmid = hal.next_lmid()
        dbid = self.create_project(lmid, "Web", name, description, alias, host)

        if dbid:
            module_ids = [x for x in [utils.webs.modules.get(m, 0) for m in modules] if x]
            lang_ids = [x for x in [utils.projects.langs.get(l, 0) for l in langs] if x]
            theme_ids = [x for x in [utils.projects.themes.get(t, 0) for t in themes] if x]

            query = "insert into web.webs (lmobj, domain, port, ssl_last_gen, modules, langs, themes, default_lang, default_theme, has_top, has_animations, has_domain_in_title) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id;"
            params = hal.lmobjs[lmid], domain, self.next_port(), None, module_ids, lang_ids, theme_ids, utils.projects.langs[default_lang], utils.projects.themes[default_theme], has_top, has_animations, has_domain_in_title

            if hal.db.execute(query, params)[0][0]:
                log(f"{lmid} web app created!", console=True)
                hal.create_pool(dbid)
                return

        log(f"Couldn't create web app '{lmid}'!", level=4, console=True)

    def generate_dh(self):
        if utils.isfile(utils.ssl_dir + "dhparam.pem", host=self.lmid):
            log("DH parameters are already in place!")
            yes = utils.yes_no("Purge them?")

            if yes: cmd(f"rm {utils.ssl_dir}dhparam.pem", host=self.lmid)
            else: return

        log("Generating DH params. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096", host=self.lmid)

    # Hosts
    def create_host(self, env="dev", alias=None, mem=1024, cpus=1, disk=2):
        log("Creating new VM ...", console=True)
        lmid = hal.next_lmid()
        hostname = alias if alias else lmid

        query = "select lmobj from nets where pm=%s;"
        params = self.dbid,
        vm_net_id = hal.db.execute(query, params)[0][0]

        ip = utils.get_free_ip(vm_net_id)
        utils.hosts.preseed_host(hostname, vm_net_id, ip)

        cmd(f"sudo virt-install " + ' '.join([
            f"--name {hostname}",
            f"--memory {mem}",
            f"--vcpus {cpus}",
            f"--cdrom {utils.tmp_dir + hostname}.iso",
            "--os-variant generic",
            f"--disk {utils.vms_dir + lmid}.qcow2,size={disk},format=qcow2,cache=none",
            f"--network network={hal.pools.get(vm_net_id).lmid}",
            "--noautoconsole",
            ]), host=self.lmid)

        if utils.isfile(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid):
            mac = re.compile("<mac address='(.*?)'/>").search(utils.read(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid)).group(1)

            dbid = hal.insert_lmobj(lmid, 'Host', alias)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = dbid, mac, vm_net_id, ip, None, utils.envs.get(env), None, None, self.dbid,

            hal.db.execute(query, params)
            self.config_dhcp()

            log(f"{hostname} VM created on {self.name}!", console=True)

        log(f"Couldn't create {hostname} VM on {self.name}!", level=4, console=True)

    # Mount
    def is_mounted(self):
        if len(os.listdir(self.mnt_dir)):
            return True
        return False

    def mount(self):
        if self.dbid == hal.host_dbid:
            log("You can't mount the host!", level=4, console=True)
        else:
            if not os.path.isdir(self.mnt_dir):
                log(f"Creating mount point at {self.mnt_dir} ...")
                cmd("mkdir " + self.mnt_dir)

            if not self.is_mounted():
                cmd(f"sshfs -p {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} hal@{self.ip}:/home {self.mnt_dir}")
                log(f"{self.name} mounted {util.now()}", console=True)
            else:
                log(f"{self.name} is already mounted!", console=True)

    def unmount(self):
        if self.dbid == hal.host_dbid:
            log("You can't unmount the host!", level=4, console=True)
        else:
            if self.is_mounted():
                cmd(f"fusermount -u {self.mnt_dir}")
                log(f"{self.name} unmounted {util.now()}", console=True)
            else:
                log(f"{self.name} is already unmounted!", console=True)

            # Double check that it's unmounted
            if os.path.isdir(self.mnt_dir) and not self.is_mounted():
                log(f"Removing mount point from {self.mnt_dir} ...")
                cmd("rmdir " + self.mnt_dir)

    # System
    def update(self):
        log(f"Updating {self.lmid} ...", console=True)
        cmd("apt update && apt upgrade -y", host=self.lmid)

    def reboot(self):
        log(f"Rebooting {self.lmid} ...", console=True)
        cmd("sudo systemctl reboot now", host=self.lmid)

    def check(self):
        if not self.ssh_port:
            self.config_ssh_server()

        if not self.pg_port:
            self.config_postgres()

        print(cmd("echo 1", catch=True, host=self.lmid))

class ProjectUtils:
    langs = {}
    themes = {}

utils.projects = ProjectUtils()

class Project(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        self.repo_dir = utils.projects_dir + self.lmid + '/'
        self.log_file = utils.logs_dir + self.lmid + ".log"

    def save(self, message="Updated files"):
        # Will be replaced with the API method
        git_cmd = f"git --git-dir={self.repo_dir}.git/ --work-tree={self.repo_dir} " + "{}"
        cmd(git_cmd.format(f"add {self.repo_dir}*"))
        cmd(git_cmd.format(f"commit -m '{message}'"))
        cmd(git_cmd.format("push"))
        log(f"Saved {self.name} on Gitlab ...", console=True)

class WebUtils:
    methods = "get", "put", "post", "delete"
    modules = {}

utils.webs = WebUtils()

class Web(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

        query = "select a.id, b.dev_version, c.id, b.prod_version, b.name, b.description, d.name, e.port, e.modules, e.langs, e.themes, e.default_lang, e.default_theme, e.has_top, e.has_animations, e.title_format from lmobjs a, project.projects b, lmobjs c, domains d, web.webs e where a.id=b.dev_host and c.id=b.prod_host and e.domain=d.id and e.lmobj=%s;"
        params = dbid,
        self.dev_host_id, self.dev_version, self.prod_host_id, self.prod_version, self.name, self.description, self.domain, self.port, self.module_ids, self.lang_ids, self.theme_ids, self.default_lang_id, self.default_theme_id, self.has_top, self.has_animations, self.title_format = hal.db.execute(query, params)[0]

        dev_domain = self.domain.split('.')
        dev_domain.insert(-2, 'dev')
        self.dev_domain = '.'.join(dev_domain)

        self.modules = [utils.webs.modules[m] for m in self.module_ids]
        self.langs = [utils.projects.langs[l] for l in self.lang_ids]
        self.themes = [utils.projects.themes[t] for t in self.theme_ids]
        self.default_lang = utils.projects.langs[self.default_lang_id]
        self.default_theme = utils.projects.themes[self.default_theme_id]

        self.ssl_dir = utils.ssl_dir + self.domain
        self.dev_ssl_dir = utils.ssl_dir + self.dev_domain
        self.app_dir = self.repo_dir + "src/app/"
        self.html_dir = self.app_dir + "html/"

        #self.db = Db(self.dbid)
        #self.check()

    def default(self):
        log(f"Setting {self.lmid}.{self.domain} to 'Hello World' ...", console=True)

        app_main = util.read(hal.tpl_dir + "web/app/app.py") \
            .replace("%APP_DIR", self.app_dir) \
            .replace("%LOG_FILE", self.log_file)
        util.write(self.app_dir + "app.py", app_main)

        settings = {
            "lmid": self.lmid,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "host": hal.lmobjs[self.host][0],
            "log_level": 2,
            "modules": self.modules,
            "langs": self.langs,
            "themes": self.themes,
            "default_lang": hal.putil.langs[self.default_lang_id],
            "default_theme": hal.putil.themes[self.default_theme_id],
            "has_top": self.has_top,
            "has_animations": self.has_animations,
            "has_domain_in_title": self.has_domain_in_title,
            }

        util.write(self.app_dir + "settings.ast", settings)

        query = "select host, port, password from dbs where lmobj=%s;"
        params = self.dbid,
        db_data = hal.db.execute(query, params)[0]
        db_details = {
            "host": db_data[0],
            "port": db_data[1],
            "password": db_data[2]
        }

        util.write(self.app_dir + "db.ast", db_details)

        # Delete old html
        # To do: move files to Hal's trash for reversal
        cmd(f"rm -r {self.app_dir}html/")
        cmd(f"rsync -r {hal.tpl_dir}web/app/html/* {self.app_dir}html/")

        self.update_html()
        self.restart()

    def update(self, data):
        if data in ("html",):
            getattr(self, "update_" + data)()

    def update_html(self):
        log(f"Updating html for {self.lmid}.{self.domain} ...")

        self.db.erase()
        self.db.build()

        query = f"insert into methods (name) values {', '.join(['(%s)' for m in hal.wutil.methods])} returning id, name;"
        params = hal.wutil.methods
        methods = dict(self.db.execute(query, params))
        methods.update(util.reverse_dict(methods))

        query = f"insert into langs (code) values {', '.join(['(%s)' for l in self.langs])} returning id, code;"
        params = self.langs
        langs = dict(self.db.execute(query, params))
        langs.update(util.reverse_dict(langs))

        query = f"insert into modules (name) values {', '.join(['(%s)' for m in self.modules])} returning id, name;"
        params = self.modules
        modules = dict(self.db.execute(query, params))
        modules.update(util.reverse_dict(modules))

        app_wrapper = util.read(f"{hal.tpl_dir}web/app/html/wrapper.html")
        if self.has_top:
            top_button = YML2HTML(util.read(f"{hal.tpl_dir}web/app/html/top-button.yml"), self.default_lang, self.default_lang).html
        else:
            top_button = ""

        def solve_section(section_dir, section_name, parent_id):
            query = "insert into sections (name, parent) values (%s, %s) returning id;"
            params = section_name, parent_id
            section_id = self.db.execute(query, params)[0][0]

            pages = [p for p in os.listdir(section_dir) if p.endswith(".yml")]
            for page in pages:
                filename = page.split(".")[0].split("-")
                name, method = filename[:2]
                first = len(filename) == 3

                if name == "lm_wrapper":
                    continue

                meta, yml = util.read(section_dir + page).split("----")
                meta = yaml.safe_load(meta)
                for lang in self.langs:
                    body = YML2HTML(yml, self.default_lang, lang).html
                    app_header = YML2HTML(util.read(f"{self.html_dir}app-header.yml"), self.default_lang, lang).html
                    app_footer = YML2HTML(util.read(f"{self.html_dir}app-footer.yml"), self.default_lang, lang).html
                    copyright = YML2HTML(util.read(f"{self.html_dir}copyright.yml"), self.default_lang, lang).html
                    cookies_notice = YML2HTML(util.read(f"{self.html_dir}cookies-notice.yml"), self.default_lang, lang).html

                    title = meta["title"].get(lang, meta["title"][self.default_lang])
                    if self.has_domain_in_title:
                        title += " | " + self.domain

                    description = meta["description"].get(lang, meta["description"][self.default_lang])
                    permalink = ""
                    og_url = ""
                    og_image = ""
                    alt = ''.join([f'<link rel="alternate" href="/{l}/{permalink}" hreflang="{l}"' for l in self.langs if l != lang])

                    html = app_wrapper\
                        .replace("%LANG", lang)\
                        .replace("%DEFAULT_THEME", self.default_theme)\
                        .replace("%ALT", alt)\
                        .replace("%NAME", self.name)\
                        .replace("%TITLE", title)\
                        .replace("%DESCRIPTION", description)\
                        .replace("%OG_URL", og_url)\
                        .replace("%OG_IMAGE", og_image)\
                        .replace("%APP_HEADER", app_header)\
                        .replace("%BODY", body)\
                        .replace("%APP_FOOTER", app_footer)\
                        .replace("%COPYRIGHT", copyright)\
                        .replace("%TOP_BUTTON", top_button)\
                        .replace("%COOKIES_NOTICE", cookies_notice)

                    if self.has_top:
                        html = html.replace("%PERMALINK", permalink)

                    query = "insert into pages (name, module, section, method, lang, first, html) values (%s, %s, %s, %s, %s, %s, %s);"
                    params = name, modules[meta["module"]], section_id, methods[method], langs[lang], first, html,
                    self.db.execute(query, params)

            for section in [s for s in os.listdir(section_dir) if os.path.isdir(section_dir + s + '/')]:
                solve_section(section_dir + section + '/', section, section_id)

        for section in [s for s in os.listdir(self.html_dir) if os.path.isdir(self.html_dir + s + '/')]:
            solve_section(self.html_dir + section + '/', section, 0)

    def ssl(self):
        if not os.path.isdir(self.ssl_dir):
            cmd("mkdir " + self.ssl_dir)

        # Production certificates
        if hal.pools[self.host].env == hal.envs.get("prod"):
            log(f"Generating Let's Encrypt SSL certs for {self.lmid}.{self.domain}. This may take a while ...", console=True)

        # Dev and test certificates
        else:
            log(f"Generating self-signed SSL certs for {self.lmid}.{self.domain}. This may take a while ...", console=True)
            cmd(f'sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout {self.ssl_dir}privkey.pem -out {self.ssl_dir}pubkey.pem -subj "/C=RO/ST=Bucharest/L=Bucharest/O={hal.domain}/CN={self.lmid}.{self.domain}"')

        query = "update projects.webs set ssl_last_gen=%s where lmobj=%s;"
        params = datetime.now(), self.dbid,
        hal.db.execute(query, params)

    def build(self):
        log(f"Building {self.lmid} ...", console=True)
        dir_tree = (
            "docs/",
            "src/",
                "src/app/",
                    "src/app/html/",
                "src/assets/",
                    "src/assets/icons/",
                    "src/assets/img/",
                    "src/assets/css/",
                    "src/assets/js/",
            "LICENSE",
            "README.md",
            )

        for node in dir_tree:
            node = self.repo_dir + node
            if not util.isfile(node):
                if node.endswith('/'):
                    cmd(f"mkdir " + node)
                else:
                    cmd(f"touch " + node)

        self.default()
        self.config()

    def restart(self):
        log(f"Restarting {self.lmid} ...", console=True)
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;")
        cmd(f"sudo supervisorctl restart {self.lmid}")

    def config(self, service=""):
        if not service: all = True
        else: all = False

        services = ("uwsgi", "nginx", "supervisor")
        if all:
            for s in services:
                getattr(self, "config_" + s)()
        elif service in services:
            getattr(self, "config_" + service)()
        else:
            log(f"Can't config service '{service}'!", level=4, console=True)

    def config_uwsgi(self):
        log(f"Configuring uWSGI for {self.lmid}.{self.domain} ...", console=True)
        uwsgi_config = util.read(hal.tpl_dir + "web/app/uwsgi.tpl") \
            .replace("%LMID", self.lmid) \
            .replace("%PORT", str(self.port)) \
            .replace("%APP_DIR", self.app_dir) \
            .replace("%PROJECTS_DIR", hal.projects_dir) \
            .replace("%LOG_FILE", hal.logs_dir + self.lmid + ".log")
        util.write(self.app_dir + "uwsgi.ini", uwsgi_config)
        hal.pools[self.host].restart("supervisor")

    def config_supervisor(self):
        log(f"Configuring Supervisor for {self.lmid} ...", console=True)
        supervisor_config = util.read(hal.tpl_dir + "web/app/supervisor.tpl") \
            .replace("%LMID", self.lmid) \
            .replace("%APP_DIR", self.app_dir) \
            .replace("%PROJECTS_DIR", hal.projects_dir)
        util.write(f"/etc/supervisor/conf.d/{self.lmid}.conf", supervisor_config, owner="root")
        hal.pools[self.host].restart("supervisor")

    def config_nginx(self):
        log(f"Configuring Nginx for {self.lmid}.{self.domain} ...", console=True)
        nginx_config = util.read(hal.tpl_dir + "web/app/nginx.tpl") \
            .replace("%LMID", self.lmid) \
            .replace("%PORT", str(self.port)) \
            .replace("%DOMAIN", self.domain) \
            .replace("%REPO_DIR", self.repo_dir) \
            .replace("%SSL_DIR", self.ssl_dir) \
            .replace("%HAL_SSL_DIR", hal.ssl_dir) \
            .replace("%OCSP", "on" if hal.pools[self.host].env == hal.envs.get("prod") else "off")
        util.write(f"/etc/nginx/sites-enabled/{self.lmid}", nginx_config, owner="root")
        hal.pools[self.host].restart("nginx")

    def check(self):
        is_empty = len(os.listdir(self.repo_dir)) == 2     # There's just .git

        # Has valid SSL Certificates
        # To do: check if they've expired
        if not cmd("ls " + self.ssl_dir, catch=True):
            self.ssl()

        # Assign a process port
        if not self.port:
            self.port = hal.pools[self.host].next_port()
            query = "update projects.webs set port=%s where lmobj=%s;"
            params = self.port, self.dbid,
            hal.db.execute(query, params)

            # For when I'm doing a db reset
            if not is_empty:
                self.config()

        # Check if project is initiated
        if is_empty:
            self.build()

        if not util.isfile(self.log_file):
            cmd(f"touch {self.log_file}")
            cmd("sudo chown www-data:www-data " + self.log_file)

class AppUtils:
    pass

utils.apps = AppUtils()

class App(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

class SoftUtils:
    pass

utils.softs = SoftUtils()

class Soft(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

class CLI:
    receive_command = True
    acts = {}
    objs = {}
    args = {}

    def start(self):
        log("Starting CLI ...")

        command = ""
        while self.receive_command:
            command = input(" > ")

            if command in ("q", "exit"):
                self.stop()
            elif command == "":
                continue
            else:
                self.process(command)

    def stop(self):
        log("Stopping CLI ...")
        self.receive_command = False

    def invalid(self, a=None, o=None, ao=None):
        if a and o:
            log(f"Invalid action '{a}' on object '{o}'!", level=4, console=True)
        elif a:
            log(f"Invalid action '{a}'!", level=4, console=True)
        elif o:
            log(f"Invalid object '{o}'!", level=4, console=True)
        elif ao:
            log(f"Invalid action or object '{ao}'!", level=4, console=True)

    def validate(self, command):
        # To do: Validate command
        if '""' in command:
            log("Not a valid command format!", level=4, console=True)
            return 0
        return 1

    def process_params(self, act_ids, params):
        print(act_ids, params)
        return {}

    def process(self, command):
        log("Issued command: " + command)
        if not self.validate(command): return

        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", command) if p.strip()] + ['']    # Split by spaces unless surrounded by quotes

        lmobj_id = hal.lmobjs.get(command[0], 0)    # Try to get a lmobj

        if lmobj_id:
            # lmobj act obj    ===    lm1 restart nginx
            # lmobj act        ===    lm3 save

            lmobj, act, obj = command[:3]
            act_id = self.acts.get(act, 0)

            if not act_id:
                return self.invalid(a=act)

            # Find object id from particular command
            module_id = hal.lmobjs[lmobj_id][1]      # Get Host module id
            obj_id = self.objs[module_id].get(obj, 0)    # Get nginx object id

            if obj_id == 0:    # It can be ''
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[1]:
                return self.invalid(a=act, o=lmobj)

            # Solve parameters
            try: params = command[2:]
            except: params = []

            params = self.process_params(obj_data[2], params)

            # Call the method
            if obj == '':
                getattr(hal.pools[lmobj_id], act)(**params)
            else:
                getattr(hal.pools[lmobj_id], act + '_' + obj)(**params)

        else:
            # act obj    ===    create net
            # obj        ===    status

            act, obj = command[:2]
            act_id = self.acts.get(act, 0)

            if not act_id:
                return self.invalid(ao=act)

            module_id = 0
            module_ids = [x for x in utils.get_keys(self.objs) if hal.modules[x][0].islower()]
            obj_id = 0

            # Find object id from global command
            for m_id in module_ids:
                obj_id = self.objs[m_id].get(obj, 0)
                if obj_id:
                    module_id = m_id
                    module = hal.modules[m_id]
                    break

            if not obj_id:
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[1]:
                return self.invalid(a=act, o=obj)

            # Solve parameters
            try: params = command[2:]
            except: params = []

            params = self.process_params(obj_data[2], params)

            # Call the method
            if obj == '':
                getattr(hal, act)(**params)
            elif module.startswith("utils"):
                getattr(getattr(utils, module.split('.')[1]), act + '_' + obj)(**params)
            else:
                getattr(module, act + '_' + obj)(**params)

cli = CLI()

class YML2HTML:
    start_html = ""
    end_html = ""
    indent_width = 4
    box_indent = 0
    html = ""
    tags = "div", "a", "i", "span", "button", "noscript",
    attributes = "id", "class", "href",

    def __init__(self, yml, default_lang, lang):
        self.yml = yml.split('\n')
        self.default_lang = default_lang
        self.lang = lang

        self.lines = self.yml_lines()
        self.html = self.solve_box()
        #log(self.html)

    def yml_lines(self):
        line_index = 0
        while line_index < len(self.yml):
            line = self.yml[line_index]
            line_index += 1

            if not line or line.startswith("#"):
                continue
            else:
                yield line

    def solve_line(self, line):
        stripped_line = line.lstrip(' ')
        split_line = re.findall(r'(?:[^\s:"]|"(?:\\.|[^"])*")+', stripped_line)

        key = split_line[0]

        if len(split_line) == 2:
            value = split_line[1].strip()    # To do: Remove comments
        else:
            value = ""

        return int((len(line) - len(stripped_line)) / self.indent_width), key, value

    def create_tag(self, box):
        open_tag = "<"
        open_tag += box["tag"]

        for attr in self.attributes:
            if box.get(attr):
                open_tag += f' {attr}=' + box[attr]

        open_tag += ">"

        if box.get("text"):
            open_tag += box["text"]

        close_tag = f'</{box["tag"]}>'
        return open_tag, close_tag

    def solve_box(self, current_indent=None, key=None, value=None):
        box = {}
        html = ""
        stop = False
        children = False

        if not key:
            current_indent, key, value = self.solve_line(next(self.lines))

        self.box_indent = current_indent
        box["tag"] = key

        current_indent, key, value = self.solve_line(next(self.lines))
        while key not in self.tags and not stop:
            if key == "text":
                texts = {}
                while key not in self.attributes + self.tags:
                    try:
                        current_indent, key, value = self.solve_line(next(self.lines))
                    except StopIteration:
                        stop = True
                        break

                    texts[key] = value.strip('"')

                text = texts.get(self.lang, texts.get(self.default_lang))
                if box["tag"] in ("a", "button",):
                    box["text"] = text
                else:
                    box["text"] = MD2HTML(text).html

            elif key in self.attributes:
                box[key] = value

            elif key == "children":
                open_tag, close_tag = self.create_tag(box)
                html += open_tag + self.solve_box() + close_tag
                children = True

            if key not in self.tags and not stop:
                try:
                    current_indent, key, value = self.solve_line(next(self.lines))
                except StopIteration:
                    stop = True
                    break

        if not children:
            open_tag, close_tag = self.create_tag(box)
            html = open_tag + html + close_tag

        if current_indent == self.box_indent and not stop:
            html += self.solve_box(current_indent, key, value)

        return html

class MD2HTML:
    def __init__(self, md):
        self.html = md

def main():
    cl = sys.argv[1:]
    hal.start()

    if cl: cli.process(' '.join(cl))
    else: cli.start()

if __name__ == "__main__":
    main()

