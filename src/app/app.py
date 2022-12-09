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


class Hal:
    lmid = None
    version = None
    settings = None

    web_dbid = None
    net_dbid = None
    host_dbid = None
    db = None

    modules = {}
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

        for module in ('psycopg2', 'yaml'):
            globals()[module] = __import__(module)

        log("Phase 3: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

        logs.level = settings.get("log_level", 1)
        utils.nets.dhcp = settings.get("dhcp")
        utils.nets.dns = settings.get("dns")
        gitlab.domain = settings.get("gitlab_domain")
        gitlab.user = settings.get("gitlab_user")

        log("Phase 4: Loading database ...")
        self.db = Db(self.lmid)
        #self.db.erase()
        #self.db.build()

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
        for arg in hal.db.execute("select id, act, req, regex, short, long from command.args;"):
            cli.args[arg[0]] = arg[1:]    # id = act, req etc.

        log("Phase 4.10: Loading objects data ...")
        # Load lm objects
        for lmobj in self.db.execute("select id, lmid, module, alias from lmobjs order by id;"):
            self.lmobjs[lmobj[0]] = lmobj[1:]      # 1 = lm1, 10 ('app' module id), astatin
            self.lmobjs[lmobj[1]] = lmobj[0]       # lm1 = 1

            if lmobj[3]:
                self.lmobjs[lmobj[3]] = lmobj[0]   # alias = id

            if lmobj[1] == "lm2": self.web_dbid = lmobj[0]
            elif lmobj[1] == "lm3": self.net_dbid = lmobj[0]
            elif lmobj[1] == "lm4": self.host_dbid = lmobj[0]

        log("Phase 5: Checking services ...")
        #ssh.check()
        #gitlab.check()

        log("Phase 6: Creating object pools ...")
        for dbid in utils.get_keys(self.lmobjs):
            if isinstance(dbid, int):
                self.create_pool(dbid)

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
        # To do: get passwords securely
        details = utils.read(utils.src_dir + "app/db/details.ast")
        host = details['host']
        port = details['port']
        password = details['pass']

        self.conn = psycopg2.connect(f"dbname={self.lmid} user={self.lmid} host={host} password={password} port={port}")

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
                if "server closed the connection" in e:
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
    dhcp = None
    dns = None
    
    def in_subnets(self):
        subnets = []

        for x in cmd("ip a", catch=True).split(' '):
           if x.startswith(('192.168.', '172.16.', '10.')) and '/' in x:
               subnets.append(x)

        return subnets

    def set_dhcp(self):
        # To do: nmap scan, display available hosts, make install script for one
        print("SET DHCP")

utils.nets = NetUtils()


class SSH:
    keys_dir = utils.ssh_dir + 'keys/'

    def config_ssh(self, gitlab=False):
        log(f"Configuring SSH for {hal.host_lmid} ...")

        cmd(f"cp {hal.tpl_dir}ssh/client.tpl /home/{hal.user}/.ssh/config")

        config = ""
        if gitlab:
            gitlab_config = util.read(hal.tpl_dir + "ssh/gitlab.tpl")
            for privkey in cmd(f"ls {self.keys_dir}*-gitlab", catch=True).split('\n'):
                config += gitlab_config.replace("%PRIVKEY", privkey)

            util.write(hal.ssh_dir + "gitlab.conf", config)

        else:
            host_config = util.read(hal.tpl_dir + "ssh/host.tpl")

            query = "select a.lmid, b.ip, b.ssh_port from lmobjs a, guests b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,
            guests = hal.db.execute(query, params)

            for guest in guests:
                config += host_config \
                    .replace("%LMID", guest[0]) \
                    .replace("%IP", guest[1]) \
                    .replace("%PORT", guest[2]) \
                    .replace("%USER", "hal") \
                    .replace("%PUBKEY", self.keys_dir + guest[0])

            util.write(hal.ssh_dir + "hosts.conf", config)

    def create_sshkey(self, host):
        log(f"Generating SSH key to access host '{host}'. This may take a while ...", console=True)
        cmd(f'ssh-keygen -b 4096 -t ed25519 -a 100 -f {self.keys_dir + host} -q -N ""')

        if util.isfile(self.keys_dir + host):
            cmd("chmod 600 " + self.keys_dir + host)
            cmd("chmod 600 " + self.keys_dir + host + ".pub")
            self.config_ssh(gitlab = host.endswith("gitlab"))
            return 1
        else:
            log(f"Couldn't generate SSH key to access host '{host}'!", level=4)
            return 0

    def delete_sshkey(self, host):
        log(f"Removing SSH key for host '{host}' ...")

        privkey = util.keys_dir + host
        cmd(f"rm {privkey} {privkey}.pub")

        self.config_ssh(gitlab = host.endswith("gitlab"))

    def check(self):
        if not util.isfile(f"/home/{hal.user}/.ssh/config"):
            self.config_ssh()

ssh = SSH()


class GPG:
    def create_gpgkey(self, email):
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
                return self.create_gpgkey(email)
            return 0

    def delete_gpgkey(self, host):
        cmd(f"gpg2 --batch --delete-secret-keys {email}")
        cmd(f"gpg2 --batch --delete-keys {email}")

gpg = GPG()


class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

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
        cmd(f"git clone git@{self.domain}:{self.user}/{lmid}.git {utils.projects_dir}{lmid}/")

    def add_ssh_key(self, host):
        if hal.ssh.create_sshkey(host + "-gitlab"):
            data = {
                'title': host,
                'key': util.read(hal.ssh.keys_dir + host + "-gitlab.pub")
                }

            self.request(
                    method = "post",
                    endpoint = "/user/keys",
                    data = data
                    )

    def delete_ssh_key(self, host):
        hal.ssh.delete_sshkey(host + '-gitlab')
        self.request(
            method = "delete",
            endpoint = "/user/keys/" + self.get_ssh_keys(host).get('id')
            )

    def get_ssh_keys(self, host=None):
        keys = self.request(endpoint = "/user/keys")

        if host:
            key = None
            for k in keys:
                if k.get("title") == host:
                    key = k
                    break
            return key

        return keys

    def get_gpg_keys(self):
        keys = self.request(endpoint = "/user/gpg_keys")
        return keys

    def add_email(self, email):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': email}
            )

    def add_gpg_key(self, host):
        email = f"{host}@{self.domain}"
        privkey_id = hal.gpg.create_gpgkey(email)

        if privkey_id:
            pubkey = cmd("gpg2 --armor --export " + privkey_id, catch=True)

            self.add_email(email)
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

    def get_token(self):
        token_file = hal.app_dir + 'token.txt'

        # To do: Save it securely
        if not util.isfile(token_file):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token.")

            token = getpass.getpass("Token: ")
            util.write(token_file, token)

            return token
        else:
            return util.read(token_file)

    def check(self):
        if not util.isfile(f"/home/{hal.user}/.gitconfig"):
            self.config_git()

        if not self.get_ssh_keys(hal.host_lmid):
            self.add_ssh_key(hal.host_lmid)

        if not self.get_gpg_keys():
            self.add_gpg_key(hal.host_lmid)

gitlab = Gitlab()


class HostUtils:
    envs = {}

    def next_guest(self):
        # To do: check storage and memory usage
        return hal.host_dbid
        return hal.db.execute("select id from lmobjs where lmid='lmg2';")[0][0]

    def create_guest(self, alias="", private=False):
        log(f"Creating new {hal.env} guest ...")

        lmid = hal.hutil.next_lmid('Guest')
        net_id, net, ip = hal.nutil.next_ip()

        if self.create_libvirt_guest(lmid, net_id, net, ip):
            # Getting mac address
            xml_file = hal.bay_dir + 'guest.xml'
            cmd(f"sudo cp /etc/libvirt/qemu/{lmid}.xml {xml_file}")
            cmd(f"sudo chown {hal.user}:{hal.user} {xml_file}")
            mac = re.compile("<mac address='(.*?)'/>").search(util.read(xml_file)).group(1)

            dbid = hal.hutil.insert_lmobj(lmid, 'Guest', alias)

            query = "insert into guests (lmobj, net, mac, ip, env) values (%s, %s, %s, %s, %s);"
            params = dbid, net_id, mac, ip, hal.envs.get(hal.env),
            hal.db.execute(query, params)

            hal.db.execute("update nets set vacant = vacant-1 where lmobj=%s", (net_id,))

            hal.nutil.config_dhcp()

    def create_libvirt_guest(self, lmid, net_id, net, ip):
        self.preseed(lmid, net, ip)

        # https://manpages.debian.org/testing/virtinst/virt-install.1.en.html
        cmd(f"sudo virt-install " + ' '.join([
            f"--name {lmid}",
            "--memory 1024",
            "--vcpus 1",
            f"--cdrom {hal.bay_dir}guest.iso",
            "--os-variant generic",
            f"--disk {hal.guests_dir + lmid}.qcow2,size=2,format=qcow2,cache=none",
            f"--network network={hal.lmobjs[net_id][0]}",
            "--noautoconsole",
            ]))

        if util.isfile(f"/etc/libvirt/qemu/{lmid}.xml"):
            return 1
        else:
            log(f"Couldn't create {lmid} guest!", level=4, console=True)
            return 0

    def preseed(self, lmid, net, ip):
        arch = "amd" # "386"
        iso_dir = hal.bay_dir + "debian/"
        iso_file = hal.assets_dir + "debian.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"

        if util.isfile(hal.bay_dir + "guest.iso"):
            cmd(f"sudo rm {hal.bay_dir}guest.iso")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...")
            cmd("sudo rm -r " + iso_dir)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null")

        log("Creating preseed file ...")
        # util.new_pass(64)
        preseed_config = util.read(hal.tpl_dir + "preseed.tpl")\
            .replace("%IP", ip) \
            .replace("%NETMASK", str(net.netmask)) \
            .replace("%GATEWAY", str(net[1])) \
            .replace("%DNS", hal.nutil.dns) \
            .replace("%HOSTNAME", lmid) \
            .replace("%DOMAIN_NAME", hal.nutil.host_domain) \
            .replace("%ROOT_PASS", "test") \
            .replace("%ROOT_PASS_HASH", "") \
            .replace("%USER_FULLNAME", "hal") \
            .replace("%USERNAME", "hal") \
            .replace("%USER_PASS", "test") \
            .replace("%USER_PASS_HASH", "")

        util.write(preseed_file, preseed_config)

        log("Configuring boot options ...")
        util.write(isolinux_file, '\n'.join([
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

        md5sum = util.read(iso_dir + "md5sum.txt")
        md5sum = md5sum.replace(iso_dir, "./")
        util.write(iso_dir + "md5sum.txt", md5sum)

        cmd(f"chmod -w {iso_dir}md5sum.txt")

        log(f"Creating {lmid} iso image ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {hal.bay_dir}guest.iso {iso_dir[:-1]}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...")
            cmd("sudo rm -r " + iso_dir)

utils.hosts = HostUtils()


class lmObj:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]
        self.alias = hal.lmobjs[dbid][2]
        self.name = self.alias if self.alias else self.lmid

    def set_alias(self, alias):
        forbidden = "", "q", "exit"

        if alias in forbidden or alias.startswith("lm") or alias in utils.get_keys(cli.acts):
            log("Can't assign this alias!", level=4, console=True)

        elif alias in utils.get_keys(hal.lmobjs):
            log(f"Alias already in use by {hal.lmobjs[hal.lmobjs[alias]][0]}!", level=4, console=True)

        else:
            hal.lmobjs.pop(self.alias, None)
            hal.lmobjs[alias] = self.dbid
            self.alias = alias

            hal.db.execute("update lmobjs set alias=%s where id=%s;", (alias, self.dbid,))
            log(f"Alias '{alias}' set to {self.lmid}.", console=True)

    def remove_alias(self):
        hal.lmobjs.pop(self.alias, None)
        self.alias = None
        hal.db.execute("update lmobjs set alias=%s where id=%s;", (None, self.dbid,))
        log("Alias removed.", console=True)


class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, domain, gateway, lease_start, lease_end from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.domain, self.gateway, self.lease_start, self.lease_end = hal.db.execute(query, params)[0]

        #self.check()

    def start(self):
        """
        :public
        Starts the network.
        """

        if self.dbid != hal.net_dbid:
            if f"Network {self.lmid} started" in cmd("sudo virsh net-start " + self.lmid, catch=True):
                self.state = 1
                hal.db.execute("update nets set state=%s where lmobj=%s;", (self.state, self.dbid,))
                log(f"{self.lmid} net started.", console=True)
                return 1

        log(f"Couldn't start {self.lmid} net!", level=4, console=True)
        return 0

    def stop(self):
        """
        :public
        Stops the network.
        """

        if self.dbid != hal.net_dbid:
            if f"Network {self.lmid} destroyed" in cmd("sudo virsh net-destroy " + self.lmid, catch=True):
                self.state = 0
                hal.db.execute("update nets set state=%s where lmobj=%s;", (self.state, self.dbid,))
                log(f"{self.lmid} net stopped.", console=True)
                return 1

        log(f"Couldn't stop {self.lmid} net!", level=4, console=True)
        return 0

    def autostart(self):
        """
        :public
        Toggles autostart flag.
        """

        if self.dbid != hal.net_dbid:
            autolaunch = False if self.autolaunch else True
            out = cmd(f"sudo virsh net-autostart {'' if autolaunch else '--disable '}" + self.lmid, catch=True)
            if (autolaunch and f"Network {self.lmid} marked as autostarted" in out) or (not autolaunch and f"Network {self.lmid} unmarked as autostarted" in out):
                self.autolaunch = autolaunch
                hal.db.execute("update nets set autolaunch=%s where lmobj=%s;", (self.autolaunch, self.dbid,))
                log(f"{'Added' if self.autolaunch else 'Removed'} autostart flag for {self.lmid} net.", console=True)
                return 1

        log(f"Couldn't toggle 'autostart' flag for {self.lmid} net!", level=4, console=True)
        return 0

    def delete(self):
        # To do: move guests to another net
        if self.dbid != hal.net_dbid:
            if self.stop():
                if f"Network {self.lmid} has been undefined" in cmd("sudo virsh net-undefine " + self.lmid, catch=True):
                    hal.db.execute("delete from nets where lmobj=%s;", (self.dbid,))
                    log(f"{self.lmid} net deleted.", console=True)
                    hal.nutil.config_dhcp()
                    hal.hutil.destroy_pool(self.dbid)
                    return 1

        log(f"Couldn't delete {self.lmid} net!", level=4, console=True)
        return 0

    def check(self):
        if self.dbid != hal.net_dbid:
            if not util.isfile(f"/etc/libvirt/qemu/networks/{self.lmid}.xml"):
                if hal.nutil.create_libvirt_net(self.lmid, self.netmask, self.gateway):
                    self.start()
                    self.autostart()
                    hal.nutil.config_dhcp()


class Host(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select mac, storage, cpus, memory, net, ip, client, env, ssh_port, pg_port from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.storage, self.cpus, self.memory, self.net_dbid, self.ip, self.client_id, self.env, self.ssh_port, self.pg_port = hal.db.execute(query, params)[0]

        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.port, b.port from web.webs a, web.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def manage_service(self, action, service):
        log(f"Restarting {service} for {self.name} ...", console=True)
        cmd(f"sudo systemctl {action} {service} ")

    def has_storage(self, capacity):
        return True

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
        if os.path.isfile(utils.ssl_dir + "dhparam.pem"):
            log("DH parameters are already in place!")
            yes = utils.yes_no("Purge them?")

            if yes: cmd(f"rm {utils.ssl_dir}dhparam.pem")
            else: return

        log("Generating DH params. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for {self.name} ...")
        cmd(f"sudo cp {hal.tpls_dir}web/nginx.tpl /etc/nginx/nginx.conf")
        self.manage_service("restart", "nginx")

    def reload_nginx(self):
        self.manage_service("reload", "nginx")

    def start_nginx(self):
        self.manage_service("start", "nginx")

    def stop_nginx(self):
        self.manage_service("stop", "nginx")

    def restart_nginx(self):
        self.manage_service("restart", "nginx")

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
            if not utils.isfile(cfg_file + ".bak"):
                cmd(f"sudo cp {cfg_file} {cfg_file}.bak")
                cmd(f"sudo chown postgres:postgres {cfg_file}.bak")

        # Modify port in config file
        config = utils.read(config_file, True)
        for i, line in enumerate(config):
            if line.startswith('port ='):
                config[i] = f"port = {port}\n"
                break

        # Write new config file and restart service
        utils.write(config_file, config, lines=True, owner="postgres")
        cmd(f"sudo cp {hal.tpls_dir}db/pg_hba.tpl {pg_dir}pg_hba.conf")
        cmd(f"sudo chown postgres:postgres {pg_dir}pg_hba.conf")

        # Update ports in project files and in db
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))
        project_ids = [x[0] for x in hal.db.execute("select project from project.dbs where host=%s", (self.dbid,))]

        for lmid in [hal.lmobjs[dbid][0] for dbid in project_ids]:
            details_path = utils.projects_dir + lmid + "/src/app/db/details.ast"
            details = utils.read(details_path)
            details["port"] = port
            utils.write(details_path, details)

        self.manage_service("restart", "postgresql")

    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    def start_postgres(self):
        self.manage_service("start", "postgresql")

    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    # Supervisor
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    # Git
    def config_git(self):
        log(f"Configuring Git for {self.name} ...", console=True)
        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.lmid,
            "email": f"{self.lmid}@{gitlab.domain}",
            "gpg_key": gpg.get_privkey_id(self.lmid)
            })
        utils.write(f"/home/hal/.gitconfig", config)

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

    def check(self):
        pass


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
    modules = {}

utils.webs = WebUtils()


class Web(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

        query = "select a.id, b.dev_version, c.id, b.prod_version, b.name, b.description, d.name, e.port, e.modules, e.langs, e.themes, e.default_lang, e.default_theme, e.has_top, e.has_animations, e.has_domain_in_title from lmobjs a, project.projects b, lmobjs c, domains d, web.webs e where a.id=b.dev_host and c.id=b.prod_host and e.domain=d.id and e.lmobj=%s;"
        params = dbid,
        self.dev_host_id, self.dev_version, self.prod_host_id, self.prod_version, self.name, self.description, self.domain, self.port, self.module_ids, self.lang_ids, self.theme_ids, self.default_lang_id, self.default_theme_id, self.has_top, self.has_animations, self.has_domain_in_title = hal.db.execute(query, params)[0]

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

    def process_params(self, params):
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

            params = self.process_params(params)

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

            params = self.process_params(params)

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


