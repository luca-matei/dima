import sys, os, getpass, inspect, subprocess, string, pprint, ast, json, secrets, re, random, ipaddress, crypt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as tk_messagebox
from datetime import datetime, timedelta

class Utils:
    localhost = "127.0.0.1"
    abc = string.ascii_lowercase
    html_tags = "a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo", "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data", "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption", "figure", "footer", "form", "head", "header", "hgroup", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "html", "i", "iframe", "img", "input", "ins", "kbd", "keygen", "label", "legend", "li", "link", "main", "map", "mark", "menu", "menuitem", "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option", "output", "p", "param", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "section", "select", "small", "source", "span", "strong", "style", "sub", "summary", "sup", "svg", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "u", "ul", "var", "video", "wbr"
    tpl_header = ""

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

    def format_date(self, date, fmt):
        # https://miro.medium.com/max/2138/1*O7E2cZsFohFNj_oGEe-dYg.png
        return date.strftime(fmt)

    def now(self):
        return datetime.now().strftime("%d %b, %H:%M:%S")

    def read(self, path, lines=False, host=None, quiet=False):
        is_ast = path.endswith('.ast')
        is_json = path.endswith('.json')

        root = path.startswith("/etc/")
        contents = no_logs_cmd(f"{'sudo ' if root else ''}cat {path}", catch=True, host=host)

        if f"cat: {path}: No such file or directory" in contents:
            if not quiet:
                try:
                    log(f"'{path}' doesn't exist on '{host}'!", level=4, console=True)
                except:
                    print(f"Error: '{path}' doesn't exist on '{host}'!")

            if lines: return []
            else: return ""

        if is_ast:
            return ast.literal_eval(contents)

        elif is_json:
            if contents: return json.loads(contents)
            else: return ""

        elif lines:
            return contents.split('\n')

        else:
            return contents

    def write(self, path, content, lines=False, mode='w', owner="root", tpl=False, host=None):
        if tpl:
            if lines:
                content = self.tpl_header.split('\n') + ['\n\n'] + content
            else:
                content = self.tpl_header + '\n\n' + content

        is_ast = path.endswith('.ast')
        def write_contents(path, content, lines, mode):
            with open(path, mode=mode, encoding='utf-8') as f:
                if lines:
                    f.writelines(content)
                else:
                    if is_ast:
                        pprint.pprint(content, stream=f)
                    else:
                        f.write(content)

        #if host == None:
            #print("utils.write NONE!")

        if host == None or host == hal.host_lmid:
            final_path = None
            if path.startswith("/etc/"):
                final_path = path
                path = utils.tmp_dir + 'restricted'

            write_contents(path, content, lines, mode)

            if final_path:
                cmd(f"sudo mv {path} {final_path}")
                cmd(f"sudo chown {owner}:{owner} {final_path}")

        else:
            filename = "export" + (".ast" if is_ast else "")
            write_contents(self.tmp_dir + filename, content, lines, mode)
            hal.pools.get(hal.lmobjs[host]).send_file(self.tmp_dir + filename, path, owner=owner)

    def copy(self, src, dest, owner="root", host=None):
        """
            Copies files inside a host
        """

        r = " -R" if src.endswith('/') else ""
        if dest.startswith("/etc/"):
            cmd(f"sudo cp{r} {src} {dest}", host=host)
            cmd(f"sudo chown{r} {owner}:{owner} {dest}", host=host)

        else:
            cmd(f"cp{r} {src} {dest}", host=host)

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

                even = int(spaces == int(spaces))
                spaces = int(spaces)

                table_row += "|" + spaces*' ' + field + spaces*' ' + even*' '
            table_row += "|"
            table.append(table_row)
        table.append(row_sep)

        return '\n'.join(table)

    def isfile(self, path, host=None, quiet=False):
        response = cmd(f"ls {path}", catch=True, host=host)
        if "No such file or directory" in response:
            if not quiet:
                log(f"'{path}' doesn't exist!", level=3, console=True)
        elif response == path or (path.endswith("/") and response):
            return 1
        return 0

    def replace_multiple(self, text:'str', reps:'dict'):
        if reps:
            # Reps = Replacements
            reps_sorted = sorted(reps, key=len, reverse=True)
            reps_escaped = map(re.escape, reps_sorted)
            pattern = re.compile("|".join(reps_escaped))

            return pattern.sub(lambda match: str(reps[match.group(0)]), text)
        else:
            return text

    def format_tpl(self, tpl:'str', keys:'dict'):
        tpl = self.read(self.get_src_dir() + "assets/tpls/" + tpl) if tpl.endswith(".tpl") else tpl

        reps = {"%" + k.upper() + "%": v for k, v in keys.items()}
        return self.replace_multiple(tpl, reps)

    def confirm(self, question=""):
        # To do: implement number of tries (see select_opt())
        resp = ""
        yes = "y", "yes", "1",
        no = "n", "no", "0",

        log(question, level=3, console=True)

        if gui:
            return tk.messagebox.askyesno(title="Confirmation", message=question)
        else:
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

    def get_dirs(self, path, host=None):
        dirs = cmd(f"ls -d {path}*/", catch=True, host=host)
        if "No such file or directory" in dirs: dirs = []
        else: dirs = dirs.split("\n")

        return [d.split('/')[-2] for d in dirs]

    def get_files(self, path, host=None):
        # WARNING: using * will split by " ", otherwise by "\n"
        files = cmd(f"ls {path}", catch=True, host=host)
        if "No such file or directory" in files:
            files = []
        elif "\n" in files:
            files = files.split("\n")
        else:
            files = files.split(" ")
        return [f.split('/')[-1] for f in files]

    def join_modules(self, modules, module_path, file_path=None, module_host=None, file_host=None):
        mammoth = "\n\n".join([self.read(module_path + m, host=module_host) for m in modules])

        if file_path:
            self.write(file_path, mammoth, host=file_host)
        else:
            return mammoth

    def create_dir_tree(self, dir_tree, root="", host=None):
        if root and not self.isfile(root, host=host):
            cmd(f"mkdir {root}", host=host)

        for node in dir_tree:
            if root: node = root + node

            # It's a directory
            if node.endswith('/') and not self.isfile(node, host=host):
                cmd(f"mkdir {node}", host=host)

            # It's a file
            elif not self.isfile(node, host=host):
                cmd(f"touch {node}", host=host)

    def get_method_params(self, method):
        param_pos = []  # Parameter positionals
        params = dict(inspect.signature(method).parameters)
        for p in utils.get_keys(params):
            param = params[p]
            params[p] = [param.annotation, param.default]
            if param.default == inspect._empty:
                param_pos.append(param.name)

        return sorted(param_pos), params

    def md2html(self, md):
        return markdown.markdown(md, extensions=["extra"])

    def yml2html(self, yml, lang, default_lang, html_vars={}, host=None):
        if yml.endswith(".yml"): yml = self.read(yml, host=host)
        boxes = yaml.YAML(typ="safe").load(yml)
        html5 = ""
        tags = "lm_", "lminput", "lmtextarea",

        def solve_box(data):
            html = ""

            tag = data[0]
            properties = data[1]

            attrs = []
            box_html = ""
            text = ""
            header_permalink = ""

            # Solve properties
            if properties != None:
                for prop in properties:
                    if prop[0] in self.html_tags + tags:
                        box_html += solve_box(prop)

                    elif prop[0] == "id":
                        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "span") and prop[1].startswith("lmperma-"):
                            header_permalink = prop[1].replace("lmperma-", "")
                            attrs.append(("id", header_permalink))
                        else:
                            attrs.append(list(prop))

                    elif prop[0] == "text":
                        if type(prop[1]) == list:
                            texts = dict(prop[1])
                            text = texts.get(lang, texts.get(default_lang))

                            if tag not in ("a", "i", "button", "span", "h1", "h2", "h3", "h4", "h5", "h6"):
                                text = self.md2html(text)

                        else:
                            text = prop[1]

                        if header_permalink:
                            text = "<span>" + text + f"</span><a href='%PERMALINK%#{header_permalink}'><i class='fa fa-link'></i></a>"

                        text = utils.replace_multiple(text, {
                            "\\": "<br>",
                            "@": "<i class='fa fa-at'></i>"
                            })

                    else:
                        attrs.append(list(prop))

            attrs = dict(attrs)
            custom = attrs.pop("custom", "")

            if tag in ("lminput", "lmtextarea"):
                f_data = utils.webs.fields.get(attrs.get('type'), {})
                f_type = f_data.get("type")
                f_class = attrs.get('class', 'lmforms-field')
                f_placeholder = attrs.get('placeholder', "")
                f_heading = attrs.get('heading')
                required = attrs.get('required')
                f_minlen = f_data.get('minlen')
                f_maxlen = f_data.get('maxlen')

                f_minlen = f" minlength={f_minlen}" if f_minlen else ""
                f_maxlen = f" maxlength={f_maxlen}" if f_maxlen else ""

                if f_placeholder:
                    if type(f_placeholder) == list:
                        texts = dict(f_placeholder)
                        f_text = texts.get(lang, texts.get(default_lang))
                    else:
                        f_text = f_placeholder
                    f_placeholder = f" placeholder='{f_text}'"

                tag_html = [f"""<div class=\"{f_class}\">"""]

                if f_heading:
                    if type(f_heading) == list:
                        texts = dict(f_heading)
                        f_text = texts.get(lang, texts.get(default_lang))
                    else:
                        f_text = f_heading

                    f_required = """<span>*</span>""" if required else ""
                    tag_html.append(f"""<h6><span>{f_text}</span>{f_required}<span class=\"lmgrow\"></span><a href="docs/forms#{attrs.get('type')}"><i class=\"fa fa-circle-info\"></i></a></h6>""")

                if tag == "lminput":
                    tag_html.append(f"""<input type=\"{f_type}\"{f_placeholder}{f_minlen}{f_maxlen}>""")
                else:
                    tag_html.append(f"""<textarea{f_placeholder}{f_minlen}{f_maxlen}></textarea>""")

                if attrs.get("counter"):
                    tag_html.append(f"<span class='lmforms-counter'>0 / {f_data.get('maxlen')}</span>")

                tag_html.append("</div>")

                open_tag = ''.join(tag_html)
                close_tag = ""

            else:
                tag_attrs = ' '.join([f"{k}='{v}'" for k, v in attrs.items()])

                # Solve tags
                if tag in ("lm_",):
                    open_tag = ""
                    close_tag = ""
                else:
                    open_tag = f"<{tag}{' ' if tag_attrs else ''}{tag_attrs}{' ' if custom else ''}{custom}>"

                    if tag in ("meta", "link"):
                        open_tag = open_tag[:-1]
                        close_tag = " />"
                    elif tag in ("base", "input", "br", "hr"):
                        close_tag = ""
                    else:
                        close_tag = f"</{tag}>"

            html += open_tag + text + box_html + close_tag

            return html

        for box in boxes:
            html5 += solve_box(box)

        return html5

    def _cmd(self, call_info, command, catch=False, host=""):
        if call_info: call_info.append(host)
        # To do: display the functions that have called execute, isfile, send_file

        if host and host != hal.host_lmid:
            if call_info: logs._log(call_info, command)
            self.write(self.tmp_dir + "script.sh", command)
            command = f"ssh {host} 'bash -s' < {self.tmp_dir}script.sh"

        output = subprocess.run([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output.stdout = output.stdout.strip('\n')
        output.stderr = output.stderr.strip('\n')

        if call_info:
            if not command.startswith("ssh "): logs._log(call_info, command)
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
    call_info = list(inspect.getframeinfo(a.f_back)[:3])
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

    domain = None

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
        utils.tpl_header = utils.read(self.tpls_dir + "header.tpl")

        log("Phase 3: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        for attr in ("lmid", "version", "domain"):
            setattr(self, attr, settings.get(attr))

        logs.level = settings.get("log_level", 1)
        gitlab.domain = settings.get("gitlab_domain")
        gitlab.user = settings.get("gitlab_user")
        utils.hosts.domain = settings.get("hosts_domain")

        log("Phase 4: Loading database ...")
        self.db = Db(self.lmid)
        self.db.rebuild()

        self.load_database()

        log("Phase 5: Checking services ...")
        self.check()
        #ssh.check()
        gitlab.get_token()

        log("Phase 6: Creating object pools ...")
        for kind in (self.modules["Net"], self.modules["Host"], self.modules["Soft"], self.modules["App"], self.modules["Web"]):
            for dbid in utils.get_keys(self.lmobjs):
                if isinstance(dbid, int) and self.lmobjs[dbid][1] == kind:
                    self.create_pool(dbid)

        """
        log("Phase 7: Checking objects ...")
        for dbid in utils.get_keys(self.lmobjs):
            self.pools.get(dbid).check()
        """

    def load_database(self):
        log("Phase 4.1: Loading modules ...")
        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]   # 1 = utils.dbs
            self.modules[m[1]] = m[0]   # utils.dbs = 1

        log("Phase 4.2: Loading domains ...")
        for d in self.db.execute("select id, name from domains;"):
            self.domains[d[0]] = d[1]
            self.domains[d[1]] = d[0]

        log("Phase 4.3.1: Loading host environments ...")
        for e in self.db.execute("select id, name from host.envs;"):
            utils.hosts.envs[e[0]] = e[1]
            utils.hosts.envs[e[1]] = e[0]

        log("Phase 4.3.2 Loading host services ...")
        for s in self.db.execute("select id, name from host.services;"):
            utils.hosts.services[s[0]] = s[1]
            utils.hosts.services[s[1]] = s[0]

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
        for obj in hal.db.execute("select id, module, name, acts from command.objs;"):
            module_id = obj[1]
            if module_id not in module_ids:
                cli.objs[module_id] = {}
                module_ids.append(module_id)

            if obj[2] == None: name = ""
            else: name = obj[2]
            cli.objs[module_id][obj[0]] = obj[2:]    # id = name, acts, args
            cli.objs[module_id][name] = obj[0]     # name = id

        log("Phase 4.9: Loading objects data ...")
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
        log(f"Pool {dbid} created")

    def destroy_pool(self, dbid):
        self.pools.pop(dbid, None)
        log(f"Pool {dbid} destroyed")

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

        if alias in forbidden or alias.startswith("lm") or cli.acts.get(alias):
            log("Can't assign this alias!", level=4, console=True)
            return 0

        elif self.lmobjs.get(alias):
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

            if gui:
                gui.set_status(*self.levels[level], message)

        if level == 5:
            print("Exiting ...")
            sys.exit()

    def create_record(self, call_info, level, message):
        if type(call_info) == list and len(call_info) == 4: host = f" {call_info[3]}:"
        else: host = ""
        filename, lineno, function = call_info[:3]
        message = message.strip('\n')

        # function == "execute" and "Data" in message and
        if level == 2 and len(message) > 256:
            message = message[:253] + "..."

        record = f"{utils.now()} l{lineno} {function}(){host} {self.levels[level][0]}: {message}\n"

        utils.write(self.log_file, record, mode='a')

    def reset(self):
        # To do: save old log files
        utils.write(self.log_file, "")

logs = Logs()

def log(*args, **kwargs):
    a = inspect.currentframe()
    call_info = list(inspect.getframeinfo(a.f_back)[:3])
    logs._log(call_info, *args, **kwargs)

class DbUtils:
    query = """sudo -u hal psql -tAc \"{}\""""
    port_file = utils.projects_dir + "pg_port.txt"

utils.dbs = DbUtils()

class Db:
    def __init__(self, lmid, dbid=None, host=None):
        self.lmid = lmid
        self.dbid = dbid
        self.host = host
        self.db_dir = utils.projects_dir + lmid + "/src/app/db/"
        port_file = utils.projects_dir + "pg_port.txt"

        if self.lmid == hal.app_lmid:
            self.dev_host = hal.host_lmid
            self.host_id = hal.host_dbid
        else:
            self.dev_host = hal.lmobjs.get(hal.db.execute("select dev_host from project.projects where lmobj=%s;", (dbid,))[0][0])[0]
            self.host_id = hal.lmobjs.get(host)

            if not utils.read(port_file, host=host):
                hal.pools.get(self.host_id).config_postgres()

            if not cmd(utils.dbs.query.format(f"select 1 from pg_database where datname='{lmid}';"), catch=True, host=host):
                hal.pools.get(self.host_id).create_pg_role(self.lmid)
                hal.pools.get(self.host_id).create_pg_db(self.lmid)

        self.port = int(utils.read(port_file, host=host))
        self.connect()

        # Check if database is empty
        if not self.execute("select count(*) from pg_catalog.pg_tables where schemaname not in ('information_schema', 'pg_catalog');")[0][0]:
            self.build()

    def connect(self):
        try:
            if self.host and self.host != hal.host_lmid:
                ip = hal.pools.get(hal.lmobjs.get(self.host)).ip
            else:
                ip = "127.0.0.1"

            if utils.isfile(self.db_dir + "db_pass", host=self.host):
                # Password file exists
                password = utils.read(self.db_dir + "db_pass", host=self.host)
            else:
                # Password file has been removed
                if utils.confirm(f"Couldn't find password for database '{self.lmid}' on host '{self.host}'! Purge database? Manual intervention is required otherwise!"):
                    hal.pools.get(self.host_id).create_pg_role(self.lmid)
                    hal.pools.get(self.host_id).create_pg_db(self.lmid)

                    password = utils.read(self.db_dir + "db_pass", host=self.host)
                else:
                    log(f"Required manual intervention for database '{self.lmid}' on '{self.host}' to change password!", level=5, console=True)

            self.conn = psycopg2.connect(f"dbname={self.lmid} user={self.lmid} host={ip} password={password} port={self.port}")

        except Exception as e:
            log(e, level=4)
            log(f"Cannot connect to '{self.lmid}' database!", level=5, console=True)

        log(self.lmid + " database connected")

    def rebuild(self):
        self.erase()
        self.build()

    def format_table(self, table):
        self.execute(f"truncate {table};")

    def erase(self):
        log(f"Erasing '{self.lmid}' database ...", level=3, console=True)

        # Drop all user created schemas
        schemas = [x[0] for x in self.execute("select s.nspname as table_schema, s.oid as schema_id, u.usename as owner from pg_catalog.pg_namespace s join pg_catalog.pg_user u on u.usesysid = s.nspowner where nspname not in ('information_schema', 'pg_catalog', 'public') and nspname not like 'pg_toast%%' and nspname not like 'pg_temp_%%' order by table_schema;")]
        for schema in schemas:
            self.execute(f"drop schema if exists {schema} cascade;")

        # Drop all remaining user created tables
        tables = [x[0] for x in self.execute("select table_name from information_schema.tables where table_schema='public';")]
        for table in tables:
            self.execute(f"drop table if exists {table} cascade;")

        log(f"'{self.lmid}' database erased", console=True)

    def build(self):
        log(f"Building '{self.lmid}' database on '{self.dev_host}' ...", console=True)
        struct = utils.read(self.db_dir + "struct.ast", host=self.dev_host)
        default_file = self.db_dir + "default.ast"

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
        log(f"'{self.lmid}' database built on '{self.dev_host}'", console=True)

    def load(self, file):
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

        log(f"Loading '{file}' into '{self.lmid}' ...", console=True)

        db_data = utils.read(file, host=self.dev_host)
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
                    for row in table[1][2:]:    # Data rows
                        tmp_nmsp_tables = nmsp_tables
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
                                    if col:
                                        new_row.append(nmsps[i][2] + '.' + nmsps[i][0])                 # Table letter . Translated column
                                        wheres.append(nmsps[i][2] + '.' + nmsps[i][1] + f"='{col}'")    # Table letter . Column to translate
                                    else:
                                        new_row.append("null")
                                        tmp_nmsp_tables = [x for x in tmp_nmsp_tables if x[-1] != nmsps[i][2]]

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

                        self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) select {new_row} from {', '.join(tmp_nmsp_tables)} where {wheres};")
                else:
                    rows = []
                    ss = []
                    for row in table[1][2:]:
                        rows.extend([None if not value and isinstance(value, str) else value for value in row])
                        ss.append(f"({', '.join(['%s' for x in row])})")
                    ss = ', '.join(ss)

                    self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) values {ss};", rows)

        log(f"Loaded '{file}'", console=True)

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
        log(self.lmid + " database disconnected")

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
    pass

gpg = GPG()

class SSH:
    keygen = 'ssh-keygen -b 4096 -t ed25519 -a 100 -f {} -q -N ""'

    def create_ssh_key(self, name:'str', host:'str'=hal.host_lmid):
        log(f"Creating SSH Key '{name}' ...", console=True)
        privkey = utils.ssh_dir + name
        if utils.isfile(privkey, host=host):
            if utils.confirm("SSH key already exists! Overwrite it?"):
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(self.keygen.format(privkey), host=host)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)
            log(f"Created SSH Key '{name}'", console=True)
        else:
            log(f"Couldn't generate SSH Key '{name}'!", level=4, console=True)

ssh = SSH()

class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

    def __init__(self):
        pass

    def get_token(self):
        token_file = hal.app_dir + 'personal_token.txt'

        if not utils.isfile(token_file):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token")

            token = getpass.getpass("Token: ")
            utils.write(token_file, token)
            cmd("chmod 600 " + token_file)

            return token
        else:
            return utils.read(token_file)

    def request(self, host=hal.host_lmid, token=None, method="get", endpoint="", data={}):
        if not token: token = self.get_token()

        method = method.upper()
        if method not in ("GET", "POST", "PUT"):
            log(f"Invalid method '{method}'!", level=4)
            return {}

        curl = f"""curl -s --request {method} --header "PRIVATE-TOKEN: {token}" --header "Content-Type:application/json" --data '{json.dumps(data)}' --url "https://{self.domain}/api/v4{endpoint}" """

        response = cmd(curl, catch=True, host=host)
        return json.loads(response)

    def create_token(self, host_lmid, project_lmid):
        response = self.request(
            method = "post",
            endpoint = f"/projects/{self.user}%2F{project_lmid}/access_tokens",
            data = {
                "name": host_lmid,
                "scopes": ["api",],
                "access_level": 30,
                }
            )

        return response['token']

    def add_ssh_key(self, title, pubkey):
        data = {
            'title': title,
            'key': pubkey
            }

        self.request(
            host = hal.host_lmid,
            token = self.get_token(),
            method = "post",
            endpoint = "/user/keys",
            data = data
            )

    def add_gpg_key(self, email, pubkey):
        self.request(
            method = "post",
            endpoint = "/user/gpg_keys",
            data =  {'key': pubkey}
            )

    def create_project(self, data):
        self.request(
            method = "post",
            endpoint = "/projects",
            data = data
        )

        lmid = data['path']

        if self.get_projects(lmid):
            log(f"Gitlab repo '{lmid}' created!", console=True)
            return 1
        else:
            log(f"Couldn't create Gitlab repo '{lmid}'!", level=4, console=True)
            return 0

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





    def add_email(self, email):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': email}
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

    def check(self):
        if not utils.isfile("/home/hal/.gitconfig"):
            self.config_git()

        if not gitlab.get_ssh_keys(self.lmid):
            gitlab.add_ssh_key(self.lmid)

        if not gitlab.get_gpg_keys():
            gitlab.add_gpg_key(self.lmid)

        if not utils.ssh_dir + self.lmid + "-gitlab" in utils.read("/home/hal/.ssh/config"):
            self.config_ssh_client()

gitlab = Gitlab()

class HostUtils:
    envs = {}
    services = {}
    domain = None

    def create_host(self, env:'str'="dev", alias:'str'=None, mem:'int'=1024, cpus:'int'=1, disk:'int'=5):
        self.__doc__ = Host.create_host.__doc__
        # To do: choose a pm and invoke create_host()
        host_dbid = hal.lmobjs["lm4"]

        hal.pools.get(host_dbid).create_host(env, alias, mem, cpus, disk)

    def preseed_host(self, hostname, net_id, ip, ssh_port, host=hal.host_lmid):
        log(f"Preseeding '{hostname}' ...", console=True)
        # To do: preseed static ip
        arch = "amd" # "386"
        iso_dir = f"{utils.tmp_dir}debian-{utils.debian_version}/"
        iso_file = f"{utils.res_dir}debian-{utils.debian_version}.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"
        tmp_iso = utils.tmp_dir + hostname + ".iso"

        if utils.isfile(tmp_iso, host=host, quiet=True):
            log(f"Removing {tmp_iso}", level=3)
            cmd(f"sudo rm {tmp_iso}", host=host)

        if utils.isfile(iso_dir, host=host, quiet=True):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir, host=host)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null", host=host)

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
            "root_pass": crypt.crypt("test", salt=crypt.mksalt(method=crypt.METHOD_SHA512, rounds=1048576)),
            "username": "hal",
            "user_pass": crypt.crypt("test", salt=crypt.mksalt(method=crypt.METHOD_SHA512, rounds=1048576)),
            "packages": "sudo openssh-server build-essential python3 python3-dev python3-venv python3-pip postgresql libpq-dev openssl nginx supervisor git curl wget gnupg2",
            "ssh_key": utils.read(utils.ssh_dir + hostname + ".pub"),
            "ssh_port": ssh_port,
            })

        utils.write(preseed_file, preseed_config, host=host)

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
            ]), host=host)

        """
        # Adding the preseed file to Initrd
        log("Adding preseed file ...")
        cmd(f"chmod +w {iso_dir}install.{arch}/")
        cmd(f"gunzip {iso_dir}install.{arch}/initrd.gz")
        cmd(f"echo {preseed_dir}preseed.cfg | cpio -H newc -o -A -F {iso_dir}install.{arch}/initrd")
        cmd(f"gzip {iso_dir}install.{arch}/initrd")
        cmd(f"chmod -w -R {iso_dir}install.{arch}/")
        """

        # Regenerating md5sum.txt
        log("Regenerating md5sum ...")
        cmd(f"chmod +w {iso_dir}md5sum.txt", host=host)
        cmd(f"md5sum `find {iso_dir} -follow -type f` > {iso_dir}md5sum.txt", host=host)

        md5sum = utils.read(iso_dir + "md5sum.txt", host=host)
        md5sum = md5sum.replace(iso_dir, "./")
        utils.write(iso_dir + "md5sum.txt", md5sum, host=host)

        cmd(f"chmod -w {iso_dir}md5sum.txt", host=host)

        log(f"Creating {hostname}.iso ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {tmp_iso} {iso_dir[:-1]}", host=host)

        if utils.isfile(iso_dir, host=host, quiet=True):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir, host=host)

        log(f"Preseeded ISO image for '{hostname}' stored at '{tmp_iso}'", console=True)

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

    def transfer_file(self, from_path, to_path, from_host, to_host):
        transfer_path = utils.tmp_dir + "transfer/"
        if utils.isfile(transfer_path):
            cmd("rm -r " + transfer_path)

        hal.pools.get(from_host).retrieve_file(from_path, transfer_path)
        hal.pools.get(to_host).send_file(transfer_path, to_path)


utils.hosts = HostUtils()

class lmObj:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]
        self.alias = hal.lmobjs[dbid][2]
        self.name = self.alias if self.alias else self.lmid

    def set_alias(self, alias:'str'):
        log(f"Setting alias '{alias}' to '{self.lmid}' ...", console=True)
        if hal.check_alias(alias):
            hal.lmobjs.pop(self.alias, None)
            hal.lmobjs[alias] = self.dbid
            self.alias = alias

            hal.db.execute("update lmobjs set alias=%s where id=%s;", (alias, self.dbid,))
            log(f"Alias '{alias}' set to {self.lmid}", console=True)

    def delete_alias(self):
        log(f"Removing alias '{self.alias}' from '{self.lmid}'...", console=True)
        hal.lmobjs.pop(self.alias, None)
        self.alias = None
        hal.db.execute("update lmobjs set alias=%s where id=%s;", (None, self.dbid,))
        log("Alias deleted", console=True)

class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, dhcp, dns, domain, gateway, lease_start, lease_end from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.dhcp_id, self.dns_id, self.domain_id, self.gateway, self.lease_start, self.lease_end = hal.db.execute(query, params)[0]

        self.domain = hal.domains.get(self.domain_id)

        #self.check()

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
            log(f"'{pool.name}' set as DHCP server for net {self.name}", console=True)

        else:
            log(f"Couldn't set a DHCP server for net' {self.name}'", level=4, console=True)

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
    pg_version = 13

    def manage_service(self, action, service):
        messages = {
            "start": "Starting",
            "stop": "Stopping",
            "restart": "Restarting",
            "reload": "Reloading",
            "enable": "Enabling",
            "disable": "Disabling",
            }

        if service == "postgresql":
            if action == "status":
                pass
            else:
                cmd(f"sudo pg_ctlcluster {self.pg_version} main {action}", host=self.lmid)
        else:
            if action == "status":
                out = cmd(f"sudo systemctl status {service}", catch=True)
                if "active (running)" in out:
                    log(f"{service} is active", console=True)
                    return 1

                elif "failed" in out:
                    log(f"{service} failed!", level=4, console=True)
                    return 0
            else:
                msg = messages.get(action)
                log(f"{msg} {service} for '{self.name}' ...", console=True)
                cmd(f"sudo systemctl {action} {service} ", host=self.lmid)
                log(f"{msg[:-3]}ed {service} for '{self.name}'", console=True)

    # Nets
    def config_dhcp(self):
        log(f"Configuring DHCP server on '{self.name}' ...", console=True)
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
        self.manage_service("status", "isc-dhcp-server")

    def get_iface(self):
        return "ens3"

    # Firewall
    def config_firewall(self):
        log(f"Configuring Firewall for '{self.name}' ...", console=True)
        self.manage_service("enable", "nftables")

        if not utils.isfile("/etc/nft/", host=self.lmid):
            cmd("sudo mkdir /etc/nft/", host=self.lmid)

        nftables = utils.format_tpl("nftables/nftables.tpl", {
            "iface": self.get_iface(),
            "ssh_port": self.ssh_port,
            })

        utils.write("/etc/nftables.conf", nftables, host=self.lmid)
        self.send_file(hal.tpls_dir + "nftables/bogons-ipv4.tpl", "/etc/nft/bogons-ipv4.nft")
        self.send_file(hal.tpls_dir + "nftables/black-ipv4.tpl", "/etc/nft/black-ipv4.nft")
        self.manage_service("restart", "nftables")
        log(f"Configured Firewall for '{self.name}'", console=True)

    def enable_firewall(self):
        self.manage_service("enable", "nftables")

    def disable_firewall(self):
        self.manage_service("disable", "nftables")

    def start_firewall(self):
        self.manage_service("start", "nftables")

    def stop_firewall(self):
        self.manage_service("stop", "nftables")

    def restart_firewall(self):
        self.manage_service("restart", "nftables")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for '{self.name}' ...")
        self.send_file(hal.tpls_dir + "web/nginx.tpl", "/etc/nginx/nginx.conf")
        cmd("sudo rm /etc/nginx/sites-enabled/default", host=self.name)
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
        self.manage_service("status", "nginx")

    # Postgres
    def create_pg_role(self, role:'str', password:'str'=None):
        # https://www.postgresql.org/docs/current/sql-createrole.html
        log(f"Creating '{role}' Postgres role on '{self.name}' ...", console=True)
        if not password:
            password = utils.new_pass(64)

        role_query = utils.dbs.query.format(f"create role {role} with login password '{password}';")
        output = cmd(role_query, catch=True, host=self.lmid)
        if "already exists" in output:
            if utils.confirm(f"'{role}' role already exists on '{self.name}'! Purge it?"):
                cmd(utils.dbs.query.format(f"drop database if exists {role}; drop role if exists {role};"), host=self.lmid)
            else: return

            cmd(role_query, host=self.lmid)

        cmd(utils.dbs.query.format(f"grant {role} to hal;"), host=self.lmid)

        if role.startswith("lm"):
            utils.write(utils.projects_dir + role + "/src/app/db/db_pass", password, host=self.lmid)
            return password

        else:
            utils.write(utils.tmp_dir + "db_pass.tmp", password)
            log(f"Password stored in {utils.tmp_dir}db_pass.tmp!", console=True)

        log(f"Postgres role '{role}' created on '{self.name}'", console=True)

    def create_pg_db(self, db:'str'):
        log(f"Creating '{db}' Postgres database on '{self.name}' ...", console=True)
        db_query = utils.dbs.query.format(f"create database {db} owner {db} encoding 'utf-8';")
        output = cmd(db_query, catch=True, host=self.lmid)
        if "already exists" in output:
            if utils.confirm(f"'{db}' database already exists on '{self.name}'! Purge it?"):
                cmd(utils.dbs.query.format(f"drop database {db};"), host=self.lmid)
            else: return

            cmd(db_query, catch=True, host=self.lmid)

        log(f"Postgres database '{db}' created on '{self.name}'", console=True)

    def config_postgres(self):
        """
        Manages /etc/postgresql/13/main/postgresql.conf
                /etc/postgresql/13/main/pg_hba.conf
        Assigns a new port to the PostgreSQL server.
        """

        log(f"Configuring PostgreSQL for '{self.name}' ...", console=True)
        port = self.next_port(service=True)

        pg_dir = f"/etc/postgresql/{self.pg_version}/main/"
        config_file = pg_dir + "postgresql.conf"
        hba_file = pg_dir + "pg_hba.conf"

        # Create backup for default configs
        for cfg_file in (config_file, hba_file):
            if not utils.isfile(cfg_file + ".bak", host=self.lmid):
                utils.copy(cfg_file, cfg_file + ".bak", owner="postgres", host=self.lmid)

        # Modify port in config file
        config = utils.format_tpl("pg/postgresql.tpl", {
            "listen": "" if self.dbid == hal.host_dbid else "," + self.ip,
            "port": port
            })

        # Allow remote access
        hba = utils.format_tpl("pg/pg_hba.tpl", {
            "remote_auth": "" if self.dbid == hal.host_dbid else f"host all all {hal.pools.get(hal.host_dbid).ip}/32 scram-sha-256"
            })

        # Write new config file and restart service
        utils.write(config_file, config, owner="postgres", tpl=True, host=self.lmid)
        utils.write(hba_file, hba, owner="postgres", tpl=True, host=self.lmid)

        # Update ports in Hal projects and in db
        utils.write(utils.dbs.port_file, str(port), host=self.lmid)
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))
        log(f"Assigned Postgres port {port} to '{self.name}'", console=True)

        self.pg_port = port
        self.manage_service("restart", "postgresql")

        query = utils.dbs.query.replace("hal", "postgres")
        has_db = cmd(query.format(f"select 1 from pg_database where datname='hal';"), catch=True, host=self.lmid)

        if not has_db:
            cmd(query.format(f"create role hal with login createdb createrole password '{utils.new_pass(64)}';"), host=self.lmid)
            cmd(query.format("create database hal owner hal encoding 'utf-8';"), host=self.lmid)

        log(f"Configured PostgreSQL for '{self.name}'", console=True)

    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    def start_postgres(self):
        self.manage_service("start", "postgresql")

    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    def status_postgres(self):
        self.manage_service("status", "postgresql")

    # Supervisor
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    def status_supervisor(self):
        self.manage_service("status", "supervisor")

    # SSH
    def restart_ssh(self):
        self.manage_service("restart", "ssh")

    def config_ssh_client(self):
        if not utils.isfile("/home/hal/.ssh/", host=self.lmid):
            cmd("mkdir /home/hal/.ssh/", host=self.lmid)

        log(f"Configuring SSH Client for '{self.name}' ...", console=True)
        hosts = []

        if self.dbid == hal.host_dbid:
            query = "select a.lmid, a.alias, b.ip, b.ssh_port from lmobjs a, host.hosts b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,

            for host in hal.db.execute(query, params):
                hosts.append(utils.format_tpl("ssh/host.tpl", {
                    "lmid": host[0],
                    "ip": host[2],
                    "port": host[3],
                    "user": "hal",
                    "privkey": utils.ssh_dir + host[0],
                    }))

                if host[1]:
                    hosts.append(utils.format_tpl("ssh/host.tpl", {
                        "lmid": host[1],
                        "ip": host[2],
                        "port": host[3],
                        "user": "hal",
                        "privkey": utils.ssh_dir + host[0],
                    }))

        hosts.append(utils.format_tpl("ssh/host.tpl", {
            "lmid": gitlab.domain,
            "ip": gitlab.domain,
            "port": 22,
            "user": "git",
            "privkey": utils.ssh_dir + self.lmid + "-gitlab",
            }))

        hosts = '\n\n'.join(hosts)

        utils.write("/home/hal/.ssh/config", hosts, tpl=True, host=self.lmid)
        self.update_hosts_file()

        log(f"Configured SSH Client for '{self.name}'", console=True)

    def config_ssh_server(self):
        if self.ssh_port == -1:
            log(f"'{self.name}' is not a SSH Server!", level=4, console=True)
        else:
            log(f"Configuring SSH Server for '{self.name}' ...", console=True)
            port = self.next_port(service=True)
            self.port = port

            hal.db.execute("update host.hosts set ssh_port=%s where lmobj=%s;", (port, self.dbid))

            config = utils.format_tpl("ssh/server_config.tpl", {
                "port": port,
                })

            utils.write("/etc/ssh/sshd_config", config, tpl=True, host=self.lmid)
            self.config_firewall()
            self.restart_ssh()
            hal.pools.get(hal.host_dbid).config_ssh_client()

            log(f"Configured SSH Server for '{self.name}'", console=True)

    def create_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Generating SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'. This may take a while ...", console=True)

        host = self.lmid if for_gitlab else hal.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        if utils.isfile(privkey, host=host):
            if utils.confirm("SSH key already exists! Overwrite it?"):
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(ssh.keygen.format(privkey), host=host)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)

            log(f"SSH Key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}' generated", console=True)

            log(f"\nUse the following command to copy the key manually. Beware of the user name.\n$ ssh-copy-id -i {privkey}.pub dima@{self.ip}\n")

            if for_gitlab:
                self.config_ssh_client()
                gitlab.add_ssh_key(self.lmid, utils.read(utils.ssh_dir + self.lmid + "-gitlab.pub", host=self.lmid))
            else:
                hal.pools.get(hal.host_dbid).config_ssh_client()

            return 1
        else:
            log(f"Couldn't generate SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'!", level=4, console=True)

            return 0

    def delete_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Removing {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}' ...", console=True)

        host = self.lmid if for_gitlab else hal.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        cmd(f"rm {privkey} {privkey}.pub", host=host)

        log(f"Removed {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}'", console=True)

    ## GPG
    def get_gpg_pubkey(self, email:'str'=None):
        log(f"Getting GPG pubkey for {email} ...", console=True)
        if not email: email = self.email
        pubkey_path = utils.tmp_dir + "gpg_pubkey"
        output = cmd(f"gpg2 --export -a {self.get_gpg_key_id(email)} > {pubkey_path}", catch=True, host=self.lmid)

        if "nothing exported" in output:
            log(f"Couldn't get GPG pubkey for {email}!", level=4, console=True)

        else:
            log(f"GPG pubkey for {email} saved at {pubkey_path}!", console=True)
            return utils.read(pubkey_path, host=self.lmid)

    def get_gpg_key_id(self, email:'str'=None):
        if not email: email = self.email
        key_id = cmd(f"gpg2 --list-keys --keyid-format LONG {email}", catch=True, host=self.lmid)

        if "No public key" in key_id:
            if utils.confirm(f"Couldn't find GPG key for '{email}'! Create one?"):
                return self.create_gpg_key(email)
            return 0
        else:
            return re.findall(r'\bpub   rsa4096/\w+', key_id)[0].split('/')[1]

    def create_gpg_key(self, email:'str'=None):
        if not email: email = self.email
        log(f"Generating GPG Key for '{email}'. This may take a while ...", console=True)

        key_config = utils.format_tpl("gpg-key.tpl", {
            "user": email.split('@')[0],
            "email": email
            })
        utils.write(utils.tmp_dir + "gpg_batch", key_config, host=self.lmid)

        log(f"Generated GPG Key for '{email}'", console=True)

        cmd(f"gpg2 --batch --gen-key {utils.tmp_dir}gpg_batch", host=self.lmid)
        key_id = self.get_gpg_key_id(email)
        log(f"Key ID: {key_id}", console=True)

        return key_id

    def delete_gpg_key(self, email:'str'=None):
        log(f"Removing GPG Key for '{email}' ...", level=3, console=True)
        if not email: email = self.email
        cmd(f"gpg2 --batch --delete-secret-keys {email}", host=self.lmid)
        cmd(f"gpg2 --batch --delete-keys {email}", host=self.lmid)
        log(f"Removed GPG key for '{email}'!", level=3, console=True)


class Host(lmObj, HostServices):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select mac, net, ip, client, env, ssh_port, pg_port, pm from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.net_id, self.ip, self.client_id, self.env_id, self.ssh_port, self.pg_port, self.pm_id = hal.db.execute(query, params)[0]

        self.env = utils.hosts.envs.get(self.env_id)
        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.email = self.lmid + "@" + utils.hosts.domain
        self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.dev_port, a.prod_port, b.port from web.webs a, project.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def has_storage(self, capacity):
        return True

    # Projects
    def create_project(self, lmid, module, alias, name, description):
        if gitlab.create_project(data={
            'path': lmid,
            'name': name,
            'description': description,
            'visibility': 'private',
            'initialize_with_readme': True,
            }):

            dbid = hal.insert_lmobj(lmid, module, alias)

            query = f"insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = dbid, self.dbid, 0.1, self.dbid, 0.1, name, description,
            hal.db.execute(query, params)

            self.clone_repo(lmid)
            return dbid

        return 0

    def clone_repo(self, path:'str'):
        log(f"Cloning '{path}' Gitlab repository ...", console=True)
        cmd(f"git clone git@{gitlab.domain}:{gitlab.user}/{path}.git {utils.projects_dir}{path}/", host=self.lmid)
        log(f"'{path}' cloned", console=True)

    # Web
    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=("static",), langs:'list'=("en",), themes:'list'=("light",), default_lang:'str'="en", default_theme:'str'="light", has_animations:'bool'=False):

        # To do: validate parameters

        #if hal.domains.get(domain):
            #log("Domain already exists!", level=4, console=True)
            #return 0

        lmid = hal.next_lmid()
        dbid = self.create_project(lmid, "Web", alias, name, description)

        if dbid:
            module_ids = [x for x in [utils.webs.modules.get(m, 0) for m in modules] if x]
            lang_ids = [x for x in [utils.projects.langs.get(l, 0) for l in langs] if x]
            theme_ids = [x for x in [utils.projects.themes.get(t, 0) for t in themes] if x]

            query = "insert into web.webs (lmobj, domain, dev_port, prod_port, dev_ssl_due, prod_ssl_due, prod_state, modules, langs, themes, default_lang, default_theme, has_animations) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id;"
            params = hal.lmobjs[lmid], domain, self.next_port(), self.next_port(), None, None, 0, module_ids, lang_ids, theme_ids, utils.projects.langs[default_lang], utils.projects.themes[default_theme], has_animations,

            if hal.db.execute(query, params)[0][0]:
                log(f"{name if name else (alias if alias else lmid)} web app created!", console=True)
                hal.create_pool(dbid)
                self.update_hosts_file()
                return 1

        log(f"Couldn't create web app '{lmid}'!", level=4, console=True)

    def generate_dh(self):
        if utils.isfile(utils.ssl_dir + "dhparam.pem", host=self.lmid):
            if utils.confirm("DH parameters are already in place! Purge them?"):
                cmd(f"rm {utils.ssl_dir}dhparam.pem", host=self.lmid)
            else:
                return

        log(f"Generating DH params for '{self.name}'. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096", host=self.lmid)
        log(f"Generated DH params for '{self.name}'", console=True)

    # Hosts
    def create_host(self, env:'str'="dev", alias:'str'=None, mem:'int'=1024, cpus:'int'=1, disk:'int'=5):
        log("Creating new VM ...", console=True)
        lmid = hal.next_lmid()

        ip = utils.nets.get_free_ip(self.net_id)
        ssh.create_ssh_key(lmid)
        ssh_port = self.next_port(service=True)
        utils.hosts.preseed_host(lmid, self.net_id, ip, ssh_port, host=self.lmid)

        output = cmd(f"sudo virt-install " + ' '.join([
            f"--name {lmid}",
            f"--memory {mem}",
            f"--vcpus {cpus}",
            f"--cdrom {utils.tmp_dir + lmid}.iso",
            "--os-variant generic",
            f"--disk {utils.vms_dir + lmid}.qcow2,size={disk},format=qcow2,cache=none",
            f"--network bridge={self.lmid}",
            "--noautoconsole",
            ]), host=self.lmid)

        if utils.isfile(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid):
            mac = re.compile("<mac address='(.*?)'/>").search(utils.read(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid)).group(1)

            dbid = hal.insert_lmobj(lmid, 'Host', alias)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = dbid, mac, self.net_id, ip, None, utils.hosts.envs.get(env), ssh_port, self.next_port(service=True), self.dbid,

            hal.db.execute(query, params)
            hal.pools.get(hal.host_dbid).config_ssh_client()

            log(f"'{lmid}' VM created on '{self.name}'", console=True)
            hal.create_pool(dbid)

        else:
            log(f"Couldn't create '{lmid}' VM on '{self.name}'!", level=4, console=True)

    # Mount
    def is_mounted(self):
        if len(os.listdir(self.mnt_dir)):
            return True
        return False

    def mount(self):
        if self.dbid == hal.host_dbid:
            log("You can't mount the host!", level=4, console=True)
        else:
            if not utils.isfile(self.mnt_dir):
                log(f"Creating mount point at '{self.mnt_dir}' ...")
                cmd("mkdir " + self.mnt_dir)

            if not self.is_mounted():
                cmd(f"sshfs -p {self.ssh_port} -o allow_other,identityfile={utils.ssh_dir}{self.lmid} hal@{self.ip}:/home/hal {self.mnt_dir}")
                log(f"'{self.name}' mounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already mounted!", level=4, console=True)

    def unmount(self):
        if self.dbid == hal.host_dbid:
            log("You can't unmount the host!", level=4, console=True)
        else:
            if self.is_mounted():
                cmd(f"fusermount -u {self.mnt_dir}")
                log(f"'{self.name}' unmounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already unmounted!", level=4, console=True)

    # System
    def config_sysctl(self):
        log(f"Configuring sysctl for '{self.name}' ...", console=True)
        sysctl = utils.format_tpl("sysctl.tpl", {
            "iface": self.get_iface()
            })
        utils.write("/etc/sysctl.conf", sysctl, tpl=True, host=self.lmid)
        cmd("sudo sysctl -p", host=self.lmid)
        log(f"Configured sysctl for '{self.name}'", console=True)

    def config_grub(self):
        log(f"Configuring GRUB for '{self.name}' ...", console=True)
        self.send_file(hal.tpls_dir + "grub.tpl", "/etc/default/grub")
        cmd("sudo update-grub", host=self.lmid)
        log(f"Configured GRUB for '{self.name}'", console=True)

    def config_motd(self):
        self.send_file(hal.tpls_dir + "motd.tpl", "/etc/motd")

    def update_resources(self):
        log(f"Updating resources for '{self.name}' ...", console=True)
        if self.dbid != hal.host_dbid:
            cmd(f"rm -r {utils.res_dir}web/", host=self.lmid)
            self.send_file(utils.res_dir + "web/", utils.res_dir + "web/")
        else:
            # Download resources
            pass
        log(f"Updated resources for '{self.name}'", console=True)

    def update_hosts_file(self):
        def append_web(web):
            # Prod host
            if web[0] == self.ip:
                web[0] = "127.0.0.1"

            fill_spaces1 = (len("255.255.255.255") - len(web[0]))*' ' + spaces
            fill_spaces2 = (len("test.testing.lucamatei.shop") - len(web[2]))*' ' + spaces

            hosts.append(web[0] + fill_spaces1 + web[2] + fill_spaces2 + web[3])

            # Dev host
            if web[1] == self.ip:
                web[1] = "127.0.0.1"

            fill_spaces1 = (len("255.255.255.255") - len(web[1]))*' ' + spaces
            web[2] = "dev." + web[2]
            fill_spaces2 = (len("test.testing.lucamatei.shop") - len(web[2]))*' ' + spaces

            hosts.append(web[1] + fill_spaces1 + web[2] + fill_spaces2 + "dev." + web[3])


        log(f"Generating /etc/hosts for '{self.name}' ...", console=True)
        spaces = 4 * ' '
        hosts = [
            f"127.0.1.1{spaces}{self.lmid}.{utils.hosts.domain}{spaces*2}{self.lmid}"
            ]

        if self.name != self.lmid:
            hosts.append(f"127.0.1.1{spaces}{self.name}.{utils.hosts.domain}{spaces}{self.name}")

        host_entry = '\n'.join(hosts)
        hosts = []

        if self.dbid == hal.host_dbid:
            # Hosts
            query = "select a.ip, b.lmid, b.alias from host.hosts a, lmobjs b where b.id = a.lmobj and b.id != %s;"
            params = self.dbid,
            db_hosts = [list(h) for h in hal.db.execute(query, params)]

            for host in db_hosts:
                fill_spaces1 = (len("255.255.255.255") - len(host[0]))*' ' + spaces
                fill_spaces2 = (len("astatin") - len(host[1]))*' ' + spaces

                hosts.append(host[0] + fill_spaces1 + host[1] + '.' + utils.hosts.domain + fill_spaces2 + host[1])

                # Has alias
                if host[2]:
                    fill_spaces3 = (len("astatin") - len(host[2]))*' ' + spaces
                    hosts.append(host[0] + fill_spaces1 + host[2] + '.' + utils.hosts.domain + fill_spaces3 + host[2])

            host_entries = "\n".join(hosts)
            hosts = []

            # Web apps
            query = "select a.ip, b.ip, c.name, d.lmid from host.hosts a, host.hosts b, domains c, lmobjs d, web.webs e, project.projects f where a.lmobj = f.prod_host and b.lmobj = f.dev_host and c.id = e.domain and d.id = e.lmobj and d.id = f.lmobj;"
            db_webs = [list(h) for h in hal.db.execute(query, params)]

            for web in db_webs:
                append_web(web)
        else:
            host_entries = ""
            query = "select a.ip, b.ip, c.name, d.lmid from host.hosts a, host.hosts b, domains c, lmobjs d, web.webs e, project.projects f where a.lmobj = f.prod_host and b.lmobj = f.dev_host and c.id = e.domain and d.id = e.lmobj and d.id = f.lmobj and c.name=%s;"
            #params = utils.webs.assets_domain,
            #web = list(hal.db.execute(query, params)[0])

            #append_web(web)

        web_entries = "\n".join(hosts)

        hosts_file = utils.format_tpl("hosts.tpl", {
            "host": host_entry,
            "hosts": host_entries,
            "webs": web_entries
            })
        utils.write("/etc/hosts", hosts_file, host=self.lmid)

        log(f"Generated /etc/hosts for '{self.name}'", console=True)

    def add_user(self):
        pass

    def ping(self):
        log(f"Trying to ping '{self.name}' ...", console=True)
        if self.dbid == hal.host_dbid:
            print("It's this machine, dumbass!")
        else:
            response = cmd("echo 1", catch=True, host=self.lmid)
            if response == "1":
                log(f"Host '{self.name}' reached!", console=True)
            else:
                log(f"Couldn't reach host '{self.name}'!", level=3, console=True)

    def build_dir_tree(self):
        log(f"Creating Hal's directory tree on '{self.name}' ...", console=True)

        dir_tree = [
            utils.logs_dir,
            utils.projects_dir,
                utils.projects_dir + "pids/",
            utils.res_dir,
                utils.res_dir + "web/",
                utils.res_dir + "web/css/",
                utils.res_dir + "web/js/",
                utils.res_dir + "web/fonts/",
                utils.res_dir + "web/icons/",
            utils.ssl_dir,
            utils.tmp_dir
            ]

        if not self.pm_id:
            dir_tree.extend([utils.vms_dir])

        if self.env == "dev":
            dir_tree.extend([utils.ssh_dir])

        utils.create_dir_tree(dir_tree)
        cmd(f"sudo chown www-data:www-data {utils.projects_dir}pids", host=self.lmid)

    def build_venv(self):
        if utils.isfile(f"{utils.projects_dir}venv/", host=self.lmid):
            if utils.confirm(f"There's already a virtual environment on '{self.name}'! Purge it?"):
                cmd(f"rm -r {utils.projects_dir}venv/", host=self.lmid)
            else:
                return

        log(f"Creating virtual environment for '{self.name}' ...", console=True)
        cmd(f"python3 -m venv {utils.projects_dir}venv", host=self.lmid)

        packages = "netifaces requests uwsgi libsass ruamel.yaml psycopg2 markdown markdown-katex"

        cmd(f"{utils.projects_dir}venv/bin/pip install wheel", host=self.lmid)
        cmd(f"{utils.projects_dir}venv/bin/pip install {packages}", host=self.lmid)

        log(f"Created virtual environment for '{self.name}'", console=True)

    def config_git(self):
        log(f"Configuring Git for '{self.name}' ...", console=True)

        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.lmid,
            "email": self.email,
            "gpg_key_id": self.get_gpg_key_id(self.email),
            })

        utils.write(f"/home/hal/.gitconfig", config, tpl=True, host=self.lmid)

        exists = False
        gpg_pubkey = self.get_gpg_pubkey(self.email)
        gpg_keys = gitlab.request(endpoint = f"/user/gpg_keys")

        for k in gpg_keys:
            if k["key"] == gpg_pubkey:
                exists = True
                break

        if not exists:
            gitlab.add_gpg_key(self.email, gpg_pubkey)

        log(f"Configured Git for '{self.name}'", console=True)

    def setup(self):
        self.config_ssh_server()
        self.config_grub()
        self.config_motd()
        self.config_sysctl()

        self.build_dir_tree()
        self.build_venv()
        self.update_resources()

        self.generate_dh()
        self.config_nginx()
        self.config_postgres()

        if self.env == "dev":
            self.config_git()
            self.create_ssh_key(for_gitlab=True)

    def has_file(self, path:'str'):
        if utils.isfile(path, host=self.lmid):
            log("File exists!", console=True)

    def send_file(self, src_path:'str', dest_path:'str', owner:'str'="root"):
        is_dir = src_path.endswith('/')

        final_path = None
        if dest_path.startswith("/etc/"):
            final_path = dest_path
            dest_path = utils.tmp_dir + 'restricted' + ('/' if is_dir else '')

        cmd(f"scp {'-r ' if is_dir else ''}-P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} {src_path.rstrip('/')} hal@{self.lmid}:{dest_path.rstrip('/')}", catch=True)

        if final_path:
            cmd(f"sudo mv {dest_path} {final_path}", host=self.lmid)
            if owner != "root": cmd(f"sudo chown {owner}:{owner} {final_path}", host=self.lmid)

    def retrieve_file(self, src_path:'str', dest_path:'str'):
        is_dir = src_path.endswith('/')
        # Handle permissions
        cmd(f"scp {'-r ' if is_dir else ''}-P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} hal@{self.lmid}:{src_path.rstrip('/')} {dest_path.rstrip('/')}", catch=True)

    def status(self):
        print("OK")

    def update(self):
        log(f"Updating '{self.name}' ...", console=True)
        cmd("sudo apt update && sudo apt upgrade -y", host=self.lmid)
        log(f"Updated '{self.name}'", console=True)

    def reboot(self):
        log(f"Rebooting '{self.name}' ...", console=True)
        cmd("sudo systemctl reboot now", host=self.lmid)
        log(f"Rebooted '{self.name}'", console=True)

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

        query = "select dev_host, dev_version, prod_host, prod_version from project.projects where lmobj=%s;"
        params = self.dbid,
        self.dev_host_id, self.dev_version, self.prod_host_id, self.prod_version = hal.db.execute(query, params)[0]

        self.dev_host = hal.lmobjs[self.dev_host_id][0]
        self.prod_host = hal.lmobjs[self.prod_host_id][0]

        self.get_token()

    def get_token(self):
        token_file = self.repo_dir + "project_token.txt"
        if not utils.isfile(token_file, host=self.dev_host):
            token = gitlab.create_token(self.dev_host, self.lmid)
            utils.write(token_file, token, host=self.dev_host)
        else:
            return utils.read(token_file, host=self.dev_host)

    def save(self, message:'str'="Updated files"):
        log(f"Saving '{self.name}' on Gitlab ...", console=True)
        git_cmd = f"git --git-dir={self.repo_dir}.git/ --work-tree={self.repo_dir} " + "{}"
        cmd(git_cmd.format(f"add {self.repo_dir}*"), host=self.dev_host)
        cmd(git_cmd.format(f"commit -m '{message}'"), host=self.dev_host)
        cmd(git_cmd.format("push"), host=self.dev_host)
        log(f"Saved '{self.name}' on Gitlab", console=True)

class WebUtils:
    methods = "get", "put", "post", "delete"
    modules = {}
    states = {
        1: "Invisible",
        2: "Taken Down",
        3: "Under Maintenance",
        4: "Coming Soon",
        5: "Published"
    }
    fields = {
        "id": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 10,
            'pattern': r"""^[\d]{1,10}$""",
        },
        "cat": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 10,
            'pattern': r"""^[1-9]\d{,10}$""",
        },
        "tags": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 88,
            'pattern': r"""^([0-9]+(,[0-9]{1,10}){0,8}){0,1}$""",
        },
        "lang": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 1,
            'pattern': r"""^[\d]{1}$""",
        },
        "theme": {
            'type': 'hidden',
            'minlen': 1,
            'maxlen': 1,
            'pattern': r"""^[\d]{1}$""",
        },
        "title": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 128,
            'pattern': r"""^[\sa-zA-Z0-9ăĂâîÎşŞţŢ'".!+?-]{1,128}$""",
        },
        "user": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 64,
            'pattern': r"""^(?=.{1,64}$)(([a-z0-9._-]+)|([a-z0-9._+-]+@[a-z0-9._-]+\.[a-z]+))$""",
        },
        "username": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 64,
            'pattern': r"""^[a-z0-9._-]{1,64}$""",
        },
        "email": {
            'type': 'email',
            'minlen': 5,
            'maxlen': 64,
            'pattern': r"""^(?=.{5,64}$)[a-z0-9._+-]+@[a-z0-9._-]+\.[a-z]+$""",
        },
        "password": {
            'type': 'password',
            'minlen': 1,
            'maxlen': 128,
            'pattern': """^[\w\d~`,.!@#$%^&*()\-+=\[\]'"?<>|]{1,128}$""",
        },
        "name": {
            'type': 'text',
            'minlen': 2,
            'maxlen': 64,
            'pattern': r"""^[\sa-zA-ZăĂâîÎşŞţŢ-]{2,64}$""",
        },
        "subject": {
            'type': 'hidden',
            'minlen': 3,
            'maxlen': 32,
            'pattern': r"""^[\sa-zA-ZăĂâîÎşŞţŢ-]{3,32}$""",
        },
        "phone": {
            'type': 'tel',
            'minlen': 0,
            'maxlen': 16,
            'pattern': r"""^[\d\s+.-]{0,16}$""",
        },
        "msg": {
            'minlen': 4,
            'maxlen': 4096,
            'pattern': r"""^[\s\w\dăĂâîÎşŞţŢ~`,.!@#$%^&*()+='"?<>|:;-]{4,4096}$""",
        },
        "cedit": {
            'type': 'text',
            'minlen': 4,
            'maxlen': 16384,
            'pattern': r"""^[\s\w\dăĂâîÎşŞţŢ~`,.!@#$%^&*()+=_'"?<>|:;\/\[\]-]{4,16384}$""",
        },
        "summary": {
            'type': 'text',
            'minlen': 1,
            'maxlen': 256,
            'pattern': r"""^[\sa-zA-Z0-9ăĂâîÎşŞţŢ,.!+?-]{1,256}$""",
        },
        "img": {
            'type': 'hidden',
            'minlen': 0,
            'maxlen': 65000,
            'pattern': r"""^((data:image\/)(jpg|jpeg)(;base64){0,1},([a-zA-Z0-9\/=+|]{10,65000})){0,1}$""",
        },
        "color": {
            'type': 'color',
            'minlen': 4,
            'maxlen': 7,
            'pattern': r"""^#(?:[0-9a-fA-F]{3}){1,2}$""",
        },
    }

    def construct_yaml_map(self, self2, node):
        data = []
        yield data
        for key_node, value_node in node.value:
            key = self2.construct_object(key_node, deep=True)
            val = self2.construct_object(value_node, deep=True)
            data.append((key, val))

    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=(), langs:'list'=(), themes:'list'=(), default_lang:'str'="", default_theme:'str'="", has_animations=False):
        self.__doc__ = Host.create_web.__doc__
        # To do: choose a host and invoke create_web()
        host_dbid = hal.lmobjs["lm8"]

        hal.pools.get(host_dbid).create_host(env, alias, mem, cpus, disk)

utils.webs = WebUtils()

class Web(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

        query = "select a.name, b.dev_port, b.prod_port, b.dev_ssl_due, b.prod_ssl_due, b.prod_state, b.modules, b.langs, b.themes, b.default_lang, b.default_theme, b.has_animations from domains a, web.webs b where b.domain=a.id and b.lmobj=%s;"
        params = dbid,
        self.prod_domain, self.dev_port, self.prod_port, self.dev_ssl_due, self.prod_ssl_due, self.prod_state, self.module_ids, self.lang_ids, self.theme_ids, self.default_lang_id, self.default_theme_id, self.has_animations = hal.db.execute(query, params)[0]

        self.global_html = {}
        self.css_classes = {}
        self.dev_domain = "dev." + self.prod_domain
        self.modules = {}
        for m_id in self.module_ids:
            m_name = utils.webs.modules[m_id]
            self.modules[m_id] = m_name
            self.modules[m_name] = m_id

        self.langs = {}
        for l_id in self.lang_ids:
            l_name = utils.projects.langs[l_id]
            self.langs[l_id] = l_name
            self.langs[l_name] = l_id

        self.themes = [utils.projects.themes[t] for t in self.theme_ids]
        self.default_lang = utils.projects.langs[self.default_lang_id]
        self.default_theme = utils.projects.themes[self.default_theme_id]

        self.prod_ssl_dir = utils.ssl_dir + self.prod_domain + '/'
        self.dev_ssl_dir = utils.ssl_dir + self.dev_domain + '/'
        self.app_dir = self.repo_dir + "src/app/"
        self.html_dir = self.app_dir + "html/"

        self.db = Db(self.lmid, self.dbid, self.dev_host)
        self.prod_db = Db(self.lmid, self.dbid, self.prod_host)

        self.check()

    def check(self):
        for env in ("dev", "prod"):
            port = self.env_var(env, "port")
            host_id = self.env_var(env, "host_id")
            host = self.env_var(env, "host")
            domain = self.env_var(env, "domain")

            # Assign a process port
            if not port:
                self.assign_port()

            # Create log files
            if not utils.isfile(self.log_file, host=host):
                cmd(f"touch {self.log_file}", host=host)
                cmd(f"sudo chown www-data:www-data {self.log_file}", host=host)

            if not utils.isfile(self.app_dir + "db/db_pass", host=host):
                self.build(env)

    def build(self, env:'env'="dev", confirm:'bool'=False):
        """
            Command used when creating the web, when the structure has changed or when parts are missing.
        """
        domain = self.env_var(env, "domain")
        host = self.env_var(env, "host")
        host_id = self.env_var(env, "host_id")

        if utils.isfile(self.repo_dir, host=host):
            if not confirm:
                if not utils.confirm(f"Are you sure you want to rebuild '{domain}'?"):
                    log("Aborted", console=True)
                    return

            elif env == "dev":
                # To do : Remove everything but .git
                return

            elif env == "prod":
                cmd(f"rm -r " + self.repo_dir, host=host)

        log(f"Building '{domain}' ...", console=True)

        dir_tree = (
            "src/",
            "src/app/",
                "src/app/db/",
            )

        if env == "dev":
            dir_tree.extend((
                "docs/",
                "src/app/html/",
                "src/assets/",
                    "src/assets/icons/",
                    "src/assets/fonts/",
                    "src/assets/img/",
                    "src/assets/css/",
                    "src/assets/js/",
                "LICENSE",
                "README.md",
            ))

        utils.create_dir_tree(dir_tree, root=self.repo_dir, host=host)
        self.generate_ssl(env)

        if env == "prod":
            log("PROD")
            utils.get_dirs(self.repo_dir + "src/assets/", host=self.prod_host)
            utils.hosts.transfer_file(
                from_path = self.repo_dir + "src/assets/",
                to_path = self.repo_dir + "src/assets/",
                from_host = self.dev_host_id,
                to_host = self.prod_host_id
                )

        self.default(env)

        log(f"Built '{domain}'", console=True)

    def default(self, env:'env'="dev", confirm:'bool'=False):
        """
            Format files to Hello World
        """

        host = self.env_var(env, "host")
        host_id = self.env_var(env, "host_id")
        domain = self.env_var(env, "domain")

        if not confirm:
            if not utils.confirm(f"Are you sure you want to format '{domain}'?"):
                log("Aborted", console=True)
                return

        log(f"Setting '{domain}' to 'Hello World' ...", console=True)

        settings = {
            "lmid": self.lmid,
            "log_level": 2,
            "default_lang": self.default_lang,
            "default_theme": self.default_theme,
            }

        utils.write(self.app_dir + "settings.ast", settings, host=host)
        self.default_db(env, confirm=True)
        self.config(env)
        self.update_py(env)
        self.update_css(env)
        self.update_js(env)
        if env == "dev":
            self.default_html(confirm=True, hello=True)

        hal.pools.get(host_id).restart_supervisor()
        hal.pools.get(host_id).restart_nginx()

        log(f"Set '{domain}' to 'Hello World'", console=True)

    def default_db(self, env:"env"="dev", confirm:'bool'=False):
        host_id = self.env_var(env, "host_id")
        domain = self.env_var(env, "domain")
        db = self.env_var(env, "db")

        if not confirm:
            if not utils.confirm(f"Are you sure you want to format '{domain}' database?"):
                log("Aborted", console=True)
                return

        log(f"Formatting '{domain}' database ...", console=True)

        if env == "dev":
            host_struct_file = utils.src_dir + "assets/web/app/db/struct.ast"
            remote_struct_file = self.app_dir + "db/struct.ast"
            host_default_file = utils.src_dir + "assets/web/app/db/default.ast"
            remote_default_file = self.app_dir + "db/default.ast"

            if host_id == hal.host_dbid:
                utils.copy(host_struct_file, remote_struct_file)
                utils.copy(host_default_file, remote_default_file)
            else:
                hal.pools.get(host_id).send_file(host_struct_file, remote_struct_file)
                hal.pools.get(host_id).send_file(host_default_file, remote_default_file)

        db.rebuild()

        query = f"insert into methods (name) values {', '.join(['(%s)' for m in utils.webs.methods])};"
        params = utils.webs.methods
        db.execute(query, params)

        langs = [v for k, v in self.langs.items() if type(v)==str]
        query = f"insert into langs (code) values {', '.join(['(%s)' for l in langs])};"
        params = langs
        db.execute(query, params)

        modules = [v for k, v in self.modules.items() if type(v)==str]
        query = f"insert into modules (name) values {', '.join(['(%s)' for m in modules])};"
        params = modules
        db.execute(query, params)

        log(f"Formatted '{domain}' database ...", console=True)

    def default_html(self, confirm:'bool'=False, hello:'bool'=False):
        """
            Command only for dev environment.
        """
        # To do: Copy img dir from default assets for http pages

        if not confirm:
            if not utils.confirm(f"Are you sure you want to format '{self.dev_domain}' HTML?"):
                log("Aborted", console=True)
                return

        src_html = utils.src_dir + "assets/web/app/html/"
        dest_html = self.app_dir + "html/"
        src_img = utils.src_dir + "assets/web/assets/img/"
        dest_img = self.repo_dir + "src/assets/img/"

        if hello:
            log(f"Setting '{self.dev_domain}' to 'Hello World' ...", console=True)
            cmd(f"rm -r " + dest_html, host=self.dev_host)
            cmd(f"rm -r " + dest_img, host=self.dev_host)

            if self.dev_host_id == hal.host_dbid:
                utils.copy(src_html, dest_html)
                utils.copy(src_img, dest_img)
            else:
                hal.pools.get(self.dev_host_id).send_file(src_html, dest_html)
                hal.pools.get(self.dev_host_id).send_file(src_img, dest_img)

            log(f"Set '{self.dev_domain}' to 'Hello World.'", console=True)

        else:
            # WARNING: THIS ONLY DELETES THE FILES, IT DOESN'T COPY
            log(f"Setting '{self.dev_domain}' Global HTML to 'Hello World' ...", console=True)
            cmd(f"rm -r {self.app_dir}html/*.yml", host=self.dev_host)
            if self.dev_host_id == hal.host_dbid:
                utils.copy(src_html + "*.yml", dest_html)
            else:
                hal.pools.get(self.dev_host_id).send_file(dest_html + "*.yml", dest_html)

            log(f"Set '{self.dev_domain}' Global HTML to 'Hello World'", console=True)

        self.update_html(global_html=True)

    def update_global_html(self, env:"env"="dev"):
        domain = self.env_var(env, "domain")
        db = self.env_var(env, "db")

        log(f"Updating Global HTML for '{domain}' ...", console=True)

        self.global_html = {}
        var_files = utils.get_files(self.html_dir + "_fractions/*.yml", host=self.dev_host)
        query = "insert into fractions (name, lang, html) values (%s, %s, %s);"
        css_classes = self.css_classes if env == "prod" else {}

        # Update global and variables html
        langs = [v for k, v in self.langs.items() if type(v)==str]
        for lang in langs:
            if not self.global_html.get(lang):
                self.global_html[lang] = {}

            for var_file in var_files:
                self.global_html[lang][var_file[:-4]] = utils.replace_multiple(self.yml2html("_fractions/" + var_file, lang), css_classes)

            # Save logged user dropdown
            user_drop_html = utils.replace_multiple(self.yml2html("user-drop.yml", lang), css_classes)
            params = "user-drop", self.langs[lang], user_drop_html
            db.execute(query, params)

            # Choose language selector
            if len(langs) == 1:
                lang_selector = ""

            elif len(langs) == 2:
                if langs[0] == self.default_lang: other_lang = langs[1]
                else: other_lang = langs[0]

                if lang == langs[0]: to_lang = langs[1]
                else: to_lang = langs[0]

                lang_selector = self.yml2html("lang-switch.yml", lang)
                lang_selector = utils.format_tpl(lang_selector, {
                    "default_lang": self.default_lang.upper(),
                    "to_lang": to_lang,
                    "other_lang": other_lang.upper(),
                    })
            else:
                lang_selector = self.yml2html("lang-drop.yml", lang)

            # Choose theme selector
            if len(self.themes) == 1:
                theme_selector = ""

            elif len(self.themes) == 2:
                theme_selector = self.yml2html("theme-switch.yml", lang)
            else:
                theme_selector = self.yml2html("theme-drop.yml", lang)

            # Save language and theme selectors
            guest_drop_html = utils.format_tpl(self.yml2html("guest-drop.yml", lang), {
                "lang_selector": lang_selector,
                "theme_selector": theme_selector,
                })
            guest_drop_html = utils.replace_multiple(guest_drop_html, css_classes)
            params = "guest-drop", self.langs[lang], guest_drop_html,
            db.execute(query, params)

            app_header = utils.format_tpl(self.yml2html("app-header.yml", lang), {
                "domain": domain,
                })

            app_footer = utils.format_tpl(self.yml2html("app-footer.yml", lang), {
                "copyright_year": datetime.now().year,
                "copyright_name": '.'.join(self.prod_domain.split(".")[-2:]),
                })

            self.global_html[lang]["app-wrapper"] = "<!doctype html>" + utils.format_tpl(self.yml2html("app-wrapper.yml", lang), {
                "lang": lang,
                "default_theme": str(self.default_theme_id),
                "alt": ''.join([f'<link rel="alternate" href="/{l}/%PERMALINK%" hreflang="{l}"' for l in langs if l != lang]),
                "name": self.name,
                "hide_all": self.yml2html("hide-all.yml", lang),
                "app_header": app_header,
                "domain": self.prod_domain,
                "app_footer": app_footer,
                "top_button": self.yml2html("top-button.yml", lang),
                "cookies_notice": self.yml2html("cookies-notice.yml", lang),
                })

        log(f"Updated Global HTML for '{domain}'", console=True)

    def update_html(self, env:"env"="dev", section:'str'= "", global_html:'bool'=False):
        if env == "prod" and not self.css_classes:
            self.update_css(env)
            return

        domain = self.env_var(env, "domain")
        db = self.env_var(env, "db")

        if global_html or not self.global_html:
            db.format_table("fractions")
            self.update_global_html(env)

        log(f"Updating HTML for '{domain}' ...", console=True)
        method_ids = dict(db.execute("select name, id from methods;"))

        # Erase current html
        db.format_table("sections")
        db.format_table("pages")

        section_dirs = utils.get_dirs(self.html_dir, self.dev_host)
        section_dirs.remove("_fractions")

        langs = [v for k, v in self.langs.items() if type(v)==str]
        def solve_section(section_dir, section_name, parent_id):
            query = "insert into sections (name, parent) values (%s, %s) returning id;"
            params = section_name, parent_id
            section_id = db.execute(query, params)[0][0]

            pages = utils.get_files(section_dir + "*.yml", host=self.dev_host)
            for page in pages:
                filename = page.split(".")[0].split("-")
                name, method = filename[:2]
                first = len(filename) == 3

                if name.startswith("lm_"):
                    continue

                yml_meta, yml = utils.read(section_dir + page, host=self.dev_host).split("----")
                meta = []

                for field in yaml.safe_load(yml_meta):
                    field = list(field)
                    if type(field[1]) == list:
                        meta.append((field[0], dict(field[1])))
                    else:
                        meta.append(field)

                meta = dict(meta)
                for lang in langs:
                    body = self.yml2html(yml, lang)
                    title = meta["title"].get(lang, meta["title"][self.default_lang])
                    if meta.get("wrapper"):
                        # Save wrappers under meta["wrapper"]
                        body = self.yml2html(f"{meta['wrapper']}-{method}.yml", lang).replace("%CONTENT%", body)

                    if meta.get("aside"):
                        aside = self.yml2html(f"{meta['aside']}-{method}.yml", lang)
                    else:
                        aside = ""

                    # FORMAT TITLE
                    #if self.has_domain_in_title:
                        #title += " | " + self.domain

                    description = meta["description"].get(lang, meta["description"][self.default_lang])
                    og_url = ""
                    og_image = ""

                    html = utils.format_tpl(self.global_html[lang]["app-wrapper"], {
                        "title": title,
                        "description": description,
                        "og_url": og_url,
                        "og_image": og_image,
                        "aside": aside,
                        "body": body,
                        })

                    # Replace reusable components
                    html_vars = re.findall("%VAR-([^%]*)%", html)
                    reps = {f"%VAR-{k}%": self.global_html[lang].get(k.lower(), "NONE") for k in html_vars}

                    # Rename CSS classes
                    if env == "prod":
                        reps.update(self.css_classes)

                    html = utils.replace_multiple(html, reps)

                    query = "insert into pages (name, module, section, method, lang, first, html) values (%s, %s, %s, %s, %s, %s, %s);"
                    params = name, self.modules[meta["module"]], section_id, method_ids[method], self.langs[lang], first, html,
                    db.execute(query, params)

            for section in utils.get_dirs(section_dir, self.dev_host):
                solve_section(section_dir + section + '/', section, section_id)

        for section in section_dirs:
            solve_section(self.html_dir + section + '/', section, 0)

        log(f"Updated HTML for '{domain}'", console=True)
        self.restart(env)

    def update_css(self, env:"env"="dev"):
        """
            Command only for dev environment.
            Joins CSS files from main host and sends the result on the remote host
        """

        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")

        def rename_classes():
            for i in range(len(classes)):
                yield ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(8))

        log(f"Updating CSS for '{domain}' ...", console=True)

        scss = utils.join_modules(
            ("palettes.scss",
                "document.scss",
                "structure.scss",
                "text.scss",
                "spacing.scss",
                "objects.scss",
                "forms.scss",
                "animations.scss",
                ),
            module_path = utils.src_dir + "assets/web/assets/css/"
            )

        try:
            css = sass.compile(string=scss, output_style='compressed')
        except Exception as e:
            log("Couldn't compile Sass! Exception:\n\n" + e, level=4, console=True)
            return

        # Protect CSS
        if env == "prod":
            self.css_classes = {}
            classes = re.findall("[#\.][_a-zA-Z]+[_a-zA-Z0-9-]*[:\w\s]*\{", css)
            new_classes = rename_classes()

            for c in classes:
                if not c.startswith(".fa"):
                    c_name = c.split(' ')[0].split(":")[0][1:].replace("{", "")
                    self.css_classes[c_name] = next(new_classes)

            utils.write(
                self.repo_dir + "src/assets/css/app.css",
                utils.replace_multiple(css, self.css_classes),
                host=host
                )

            self.update_js(env)
            self.update_html(env, global_html=True)

        else:
            utils.write(self.repo_dir + "src/assets/css/app.css", css, host=host)

        log(f"Updated CSS for '{domain}'", console=True)

    def generate_ssl(self, env:'env'="dev"):
        host = self.env_var(env, "host")
        ssl_dir = self.env_var(env, "ssl_dir")
        domain = self.env_var(env, "domain")

        if not utils.isfile(ssl_dir, host=host):
            cmd("mkdir " + ssl_dir, host=host)

        # Production certificates
        #log(f"Generating Let's Encrypt SSL certs for {self.dev_domain}. This may take a while ...", console=True)

        log(f"Generating SSL certificates for '{domain}'. This may take a while ...", console=True)
        cmd(f'sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout {ssl_dir}privkey.pem -out {ssl_dir}pubkey.pem -subj "/C=RO/ST=Bucharest/L=Bucharest/O={hal.domain}/CN={domain}"', host=host)

        query = f"update web.webs set {env}_ssl_due=%s where lmobj=%s;"
        params = datetime.now() + timedelta(3*365/12-3), self.dbid,
        hal.db.execute(query, params)

        log(f"Generated SSL certificates for '{domain}'", console=True)

    def change_state(self, new_state:'web_state', confirm:'bool'=False):
        if utils.isfile(self.repo_dir, host=self.prod_host):
            if not confirm:
                if not utils.confirm(f"Are you sure you want to change current production state for '{self.prod_domain}' to {utils.webs.states[new_state]}?"):
                    log("Aborted", console=True)
                    return

        log(f"Changing '{self.prod_domain}' state to {utils.webs.states[new_state]} ...", console=True)
        self.prod_state = new_state

        if new_state == 1:
            # Remove production config files for nginx and supervisor
            # Remove from production DNS

            for p in (
                "/etc/nginx/sites-enabled/" + self.lmid,
                f"nano /etc/supervisor/conf.d/{self.lmid}.conf"
                ):

                if utils.isfile(p, host=self.prod_host):
                    cmd("sudo rm " + p, host=self.prod_host)

            hal.pools.get(self.prod_host_id).restart_nginx()
            hal.pools.get(self.prod_host_id).restart_supervisor()

        elif new_state == 5:
            # To do: Backup the database
            db_pass_path = self.app_dir + "db/db_pass"
            db_pass = utils.read(db_pass_path, host=self.prod_host)
            self.build("prod", confirm=True)
            utils.write(db_pass_path, db_pass, host=self.prod_host)

        log(f"Changed '{self.prod_domain}' state to {utils.webs.states[new_state]}.", console=True)

    def update_js(self, env:"env"="dev"):
        # To do: add manual files
        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")
        log(f"Updating JS for '{domain}' ...", console=True)

        cmd(f"rm {self.repo_dir}src/assets/js/*.js", host=host)
        src_js_dir = utils.src_dir + "assets/web/assets/js/"
        for script in utils.get_files(src_js_dir):
            utils.write(
                self.repo_dir + "src/assets/js/" + script,
                utils.replace_multiple(utils.read(src_js_dir + script), self.css_classes),
                host=host
                )

        log(f"Updated JS for '{domain}'", console=True)

    def update_py(self, env:"env"="dev", restart:'bool'=False):
        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")

        # Joins .py files from main host and sends the result on the remote host
        log(f"Updating source code for '{domain}' ...", console=True)
        utils.join_modules((
            "utils/utils.py",
            "app.py",
            "logs.py",
            "db.py",
            "html.py",
            "http.py",
            "static.py",
            "dynamic.py",
            "autho.py",
            "authe.py",
            "process.py",
            "request.py",
            "response.py",
            "main.py",
            ),
            module_path = utils.src_dir + "assets/web/app/modules/",
            file_path = self.app_dir + "app.py",
            file_host = host)

        if restart: self.restart(env)
        log(f"Updated source code for '{domain}'", console=True)

    def assign_port(self, env:"env"="dev"):
        log(f"Assigning {env} port {port} to '{domain}' ...", console=True)
        setattr(self, env + "_port", hal.pools.get(host_id).next_port())
        port = self.env_var(env, "port")

        query = f"update web.webs set {env}_port=%s where lmobj=%s;"
        params = port, self.dbid,
        hal.db.execute(query, params)

        log(f"Assigned {env} port {port} to '{domain}'", console=True)
        self.config(env)

    def config_uwsgi(self, env:'env'="dev", restart:'bool'=False):
        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")
        port = self.env_var(env, "port")

        log(f"Configuring uWSGI for '{domain}' ...", console=True)

        uwsgi_config = utils.format_tpl("web/app/uwsgi.tpl", {
            "port": str(port),
            "app_dir": self.app_dir,
            "projects_dir": utils.projects_dir,
            "lmid": self.lmid,
            "log_file": self.log_file,
            })
        utils.write(self.app_dir + "uwsgi.ini", uwsgi_config, host=host)

        if restart: self.restart(env)
        log(f"Configured uWSGI for '{domain}'", console=True)

    def config_supervisor(self, env:'env'="dev", restart:'bool'=False):
        supervisor_file = f"/etc/supervisor/conf.d/{self.lmid}.conf"
        if env == "prod" and self.prod_state == 0:
            if utils.isfile(supervisor_file, host=self.prod_host):
                cmd(f"sudo rm {supervisor_file}", host=self.prod_host)
            else:
                log(f"Production state is set to 0. Change state to make the web app available to the internet.", level=4, console=True)

        host = self.env_var(env, "host")
        host_id = self.env_var(env, "host_id")
        domain = self.env_var(env, "domain")

        log(f"Configuring Supervisor for '{domain}' ...", console=True)
        supervisor_config = utils.format_tpl("web/app/supervisor.tpl", {
            "lmid": self.lmid,
            "projects_dir": utils.projects_dir,
            "app_dir": self.app_dir,
            })
        utils.write(supervisor_file, supervisor_config, host=host)

        if restart: hal.pools.get(host_id).restart_supervisor()
        log(f"Configured Supervisor for '{domain}'", console=True)

    def config_nginx(self, env:'env'="dev", restart:'bool'=False):
        nginx_file = f"/etc/nginx/sites-enabled/{self.lmid}"
        if env == "prod" and self.prod_state == 0:
            if utils.isfile(nginx_file, host=self.prod_host):
                cmd(f"sudo rm {nginx_file}", host=self.prod_host)
            else:
                log(f"Production state is set to 0. Change state to make the web app available to the internet.", level=4, console=True)

            return

        host = self.env_var(env, "host")
        host_id = self.env_var(env, "host_id")
        domain = self.env_var(env, "domain")
        ssl_dir = self.env_var(env, "ssl_dir")
        port = self.env_var(env, "port")

        log(f"Configuring Nginx for '{domain}' ...", console=True)

        manual = self.app_dir + "manual/nginx.tpl"
        if utils.isfile(manual, host=self.dev_host, quiet=True):
            tpl = utils.read(manual, host=self.dev_host)
        else:
            tpl = "web/app/nginx.tpl"

        nginx_config = utils.format_tpl(tpl, {
            "domain": domain,
            "ssl_dir": ssl_dir,
            "hal_ssl_dir": utils.ssl_dir,
            "ocsp": "off" if env == "đev" else "on",
            "projects_dir": utils.projects_dir,
            "res_dir": utils.res_dir,
            "repo_dir": self.repo_dir,
            "port": port,
            "lmid": self.lmid
            })
        utils.write(nginx_file, nginx_config, host=host)

        if restart: hal.pools.get(host_id).restart_nginx()
        log(f"Configured Nginx for '{domain}'", console=True)

    def config(self, env:'env'="dev", restart:'bool'=False):
        self.config_uwsgi(env, restart)
        self.config_supervisor(env, restart)
        self.config_nginx(env, restart)

    def restart(self, env:'env'="dev"):
        if env == "prod" and self.prod_state != 5:
            log("No web app is running on production!", level=4, console=True)
            return

        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")

        log(f"Restarting '{domain}' ...", console=True)
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;", host=host)
        cmd(f"sudo supervisorctl restart {self.lmid}", host=host)
        log(f"Restarted '{domain}'", console=True)

    def env_var(self, env, name):
        if name == "db" and env == "dev":
            return getattr(self, name)
        else:
            return getattr(self, env + "_" + name)

    def yml2html(self, yml, lang):
        if yml.endswith(".yml"): yml = self.html_dir + yml
        return utils.yml2html(yml, lang, self.default_lang, self.global_html, self.dev_host)

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
    skip = False

    def invalid(self, a=None, o=None, ao=None, p=None, pt=None):
        if a and o:
            log(f"Invalid action '{a}' on object '{o}'!", level=4, console=True)
        elif a:
            log(f"Invalid action '{a}'!", level=4, console=True)
        elif o:
            log(f"Invalid object '{o}'!", level=4, console=True)
        elif ao:
            log(f"Invalid action or object '{ao}'!", level=4, console=True)
        elif pt:
            self.skip = True
            if pt == "missing":
                log(f"Missing positional parameter '{p}'!", level=4, console=True)
            else:
                log(f"Invalid value for parameter '{p}'. Expected type '{pt}'!", level=4, console=True)
        elif p:
            self.skip = True
            log(f"Invalid parameter '{p}'!", level=4, console=True)

    def validate(self, command):
        # To do: Validate command
        if '""' in command:
            log("Not a valid command format!", level=4, console=True)
            return 0
        return 1

    def process_args(self, module, act, obj, tmp_args):
        # Rules:
        # Put positional parameters from method header in alphabetical order

        ## Organize required parameters

        # Get method parameters
        if obj: method = getattr(module, act + '_' + obj)
        else: method = getattr(module, act)

        param_pos, params = utils.get_method_params(method)

        ## Organize given arguments

        args = {}
        skip = False  # For cases like --cpus=4
        pos_index = 0  # Index of current positional argument
        for i, a in enumerate(tmp_args):
            if skip or not a:
                skip = False
                continue

            # Of form --message="Zavalaidanga"
            if a.startswith('-') and a.endswith('='):
                skip = True
                a = a.strip('-').strip('=').replace('-', '_')
                args[a] = tmp_args[i+1]

            # Of form --cpus=4
            elif "=" in a:
                arg = a.split("=")
                arg[0] = arg[0].strip("-").replace('-', '_')
                args[arg[0]] = arg[1]

            # Of form --no-create-home
            elif a.startswith('-'):
                a = a.strip('-').replace('-', '_')
                args[a] = True

            # Positional parameter
            else:
                try:
                    args[param_pos[pos_index]] = a
                    pos_index += 1
                except IndexError:
                    return self.invalid(p=a)

        ## Validate arguments as parameters

        for a in utils.get_keys(args):
            # Check data types
            if params.get(a, False):
                arg_type = params[a][0]
                arg = args[a]
                if arg_type == 'int':
                    try: args[a] = int(arg)
                    except ValueError: return self.invalid(p=a, pt='int')

                elif arg_type == 'float':
                    try: args[a] = float(arg)
                    except ValueError: return self.invalid(p=a, pt='float')

                elif arg_type == 'bool':
                    if arg.lower() in ("1", "true", "yes", "y"):
                        args[a] = True
                    elif arg.lower() in ("0", "false", "no", "n"):
                        args[a] = False
                    else:
                        return self.invalid(p=a, pt='boolean')

                elif arg_type == "list":
                    if arg.startswith(("(", "[")) and arg.endswith((")", "]")):
                        args[a] = arg[1:-1].split(',')
                    else:
                        return self.invalid(p=a, pt='list')
                elif arg_type == "env":
                    envs = utils.get_keys(utils.hosts.envs)
                    # dev, test, prod
                    if arg in envs:
                        args[a] = arg

                    # 1, 2, 3
                    elif arg.isdigit() and int(arg) in envs:
                        args[a] = utils.hosts.envs[int(arg)]

                    else:
                        return self.invalid(p=a, pt='env')

                elif arg_type == "web_state":
                    try: args[a] = int(arg)
                    except ValueError: return self.invalid(p=a, pt='int')

                    if args[a] not in range(1, len(utils.webs.states) + 1):
                        return self.invalid(p=a, pt="web_state")

                # Remove extra quotes
                elif args[a].startswith("'"):
                    args[a] = args[a].strip("'")

                elif args[a].startswith('"'):
                    args[a] = args[a].strip('"')

            elif a == "help" and args[a] == True:
                self.skip = True
                doc = method.__doc__
                if doc: print(doc)
                else: log("No help available for this command!", level=4, console=True)
                return {}
            else:
                return self.invalid(p=a)

        # Check for missing positional parameters
        for p in param_pos:
            if not args.get(p):
                return self.invalid(p=p, pt='missing')

        return args

    def load_history(self):
        self.history = utils.read(utils.src_dir + "app/history.txt", lines=True)

    def append_history(self, command):
        if len(self.history) >= 300:
            self.history = self.history[-200:]
            utils.write(utils.src_dir + "app/history.txt", '\n'.join(self.history))

        if command not in self.history[-3:]:
            self.history.append(command)
            utils.write(utils.src_dir + "app/history.txt", command + "\n", mode="a")

    def process(self, command):
        log("Issued command: " + command)

        if not self.validate(command): return
        self.append_history(command)

        command = [p for p in re.split("( |\\\".*?\\\"|'.*?')", command) if p.strip()] + ['']    # Split by spaces unless surrounded by quotes

        lmobj_id = hal.lmobjs.get(command[0], 0)    # Try to get a lmobj

        if lmobj_id:
            # lmobj act obj    ===    lm1 restart nginx
            # lmobj act        ===    lm3 save

            lmobj, act, obj = command[:3]
            act_id = self.acts.get(act, 0)
            if obj.startswith("-"): obj = ''

            if not act_id:
                return self.invalid(a=act)

            # Find object id from particular command
            module_id = hal.lmobjs[lmobj_id][1]      # Get Host module id
            obj_id = self.objs[module_id].get(obj, 0)    # Get nginx object id

            if not obj_id:
                return self.invalid(o=obj)

            # Get command object details
            obj_data = self.objs[module_id][obj_id]

            # Check if action is valid
            if act_id not in obj_data[1]:
                return self.invalid(a=act, o=lmobj)

            # Solve arguments
            try: args = command[3:] if obj else command[2:]
            except: args = []

            params = self.process_args(hal.pools[lmobj_id], act, obj, args)
            if self.skip:
                self.skip = False
                return

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
            if obj.startswith("-"): obj = ''

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
            try: args = command[3:] if obj else command[2:]
            except: args = []

            if obj == '':
                params = self.process_args(hal, act, obj, args)

            elif module.startswith("utils"):
                params = self.process_args(getattr(utils, module.split('.')[1]), act, obj, args)

            else:
                params = self.process_args(module, act, obj, args)

            # Invalid parameters
            if self.skip:
                self.skip = False
                return

            # Call the method
            if obj == '':
                getattr(hal, act)(**params)

            elif module.startswith("utils"):
                getattr(getattr(utils, module.split('.')[1]), act + '_' + obj)(**params)

            else:
                getattr(module, act + '_' + obj)(**params)

cli = CLI()

class GUI:
    colors = {
        "blue": "#0000FF",
        "green": "#008000",
        "yellow": "#FFFF00",
        "lred": "#FF3333",
        "red": "#FF0000",
        }

    def __init__(self):
        self.root = tk.Tk()
        self.style = ttk.Style(self.root)
        self.widgets = {}
        self.lmids = {}
        self.panel_acts = {}
        self.cmd_args = {}
        self.arg_widgets = {}
        self.last_timer = None
        self.history_index = 0

        # Window geometry
        self.w_width = 800
        self.w_height = 600

        self.screen_width = 1920    # w.winfo_screenwidth()
        self.screen_height = 1080    # w.winfo_screenheight()

        self.center_x = int(self.screen_width / 2 - self.w_width / 2)
        self.center_y = int(self.screen_height / 2 - self.w_height / 2)

        # Window properties
        self.root.title("DIMA")
        self.root.resizable(True, True)
        self.root.geometry(f'{self.w_width}x{self.w_height}+{self.center_x}+{self.center_y}')
        self.root.minsize(self.w_width, self.w_height)
        self.root.maxsize(self.screen_width, self.screen_height)
        # self.w.iconbitmap('./assets/favicon.ico')

        # Style
        self.style.theme_use("clam")

        for p in ("host", "web"):
            self.lmids[p] = hal.db.execute(f"select lmid, alias from lmobjs where module=(select id from modules where name='{p.capitalize()}');")

            acts = hal.db.execute(f"select name, acts from command.objs where module=(select id from modules where name='{p.capitalize()}');")

            self.panel_acts[p] = self.panel_acts[p] = {x[0] if x[0] != None else '': [cli.acts[y] for y in x[1]] for x in acts}

        self.build_interface()
        for m in ("host", "web"):
            self.set_dropdown(f"{m}_lmid_menu")
            self.set_dropdown(f"{m}_obj_menu")


    ## INTERFACE

    def create_notebook(self, frame, **kwargs):
        return ttk.Notebook(frame)

    def create_dropdown(self, frame, text_var=None, opts=[''], command=None, **kwargs):
        text_obj = self.widgets.get(text_var)
        menu = ttk.OptionMenu(frame, text_obj, opts[0], *opts, command = command)

        return menu

    def create_text_var(self, frame, name='', value='', **kwargs):
        string_var = tk.StringVar(frame)
        self.widgets[name] = string_var
        string_var.set(value)
        return string_var

    def create_label(self, frame, text="Label", text_var=None, font=(), **kwargs):
        text_obj = self.widgets.get(text_var)
        return ttk.Label(frame, text=text, textvariable=text_obj, font=font)

    def create_input(self, frame, text_var=None, **kwargs):
        text_obj = self.widgets.get(text_var)
        return ttk.Entry(frame, textvariable=text_obj)

    def create_button(self, frame, text="Button", command=None, **kwargs):
        return ttk.Button(frame, text=text, command=command)

    def create_frame(self, frame, bg=None, **kwargs):
        style = ttk.Style()
        style.configure(f"{bg}.TFrame", background = bg)
        return ttk.Frame(frame, style=f"{bg}.TFrame")

    def build_interface(self):
        widget_names = "notebook", "frame", "label", "button", "dropdown", "input",
        pack_properties = "padx", "pady", "ipadx", "ipady", "fill", "expand", "anchor", "side",

        gui_yml = yaml.YAML(typ="safe").load(utils.read(utils.src_dir + "app/gui.yml"))

        def solve_widget(parent_frame, data):
            w_type = data[0]
            obj = None
            pack = {}
            props = {}
            to_solve = []

            for prop in data[1]:
                if prop[0] in widget_names:
                    to_solve.append(prop)

                elif prop[0] in pack_properties:
                    value = prop[1]

                    if prop[0] in ("fill", "side", "anchor"): value = getattr(tk, prop[1].upper())

                    pack[prop[0]] = value

                elif prop[0] == "command":
                    props["command"] = getattr(self, prop[1])

                elif prop[0] == "text_var":
                    text_props = dict(prop[1])
                    props["text_var"] = text_props.get("id")
                    text_obj = getattr(self, "create_text_var")(
                        parent_frame,
                        name = text_props.get("id", ""),
                        value = text_props.get("value", "")
                        )

                    if text_props.get("trace"):
                        text_obj.trace("w", getattr(self, text_props["trace"]))

                else:
                    props[prop[0]] = prop[1]

            # Create Widget
            obj = getattr(self, "create_" + w_type)(parent_frame, **props)
            if props.get("id"): self.widgets[props["id"]] = obj

            # Display widget
            obj.pack(**pack)

            # Try because it can be root
            try:
                # Add page to screen
                if parent_frame.widgetName == "ttk::notebook":
                    parent_frame.add(obj, text=props["title"])

            except Exception as e:
                print(e)

            # Bind keypresses
            if props.get("bind"):
                for b in props["bind"]:
                    obj.bind(f"<{b[0]}>", getattr(self, b[1]))

            # Focus inputs
            if props.get("focus"):
                obj.focus()

            for w_data in to_solve:
                solve_widget(obj, w_data)

        for w_data in gui_yml:
            solve_widget(self.root, w_data)


    ## DASHBOARD

    def send_mcmd(self, *args):
        cli.process(self.widgets["mcmd_input_str"].get())
        self.widgets["mcmd_input_str"].set("")
        self.history_index = 0

    def set_dropdown(self, drop_name):
        self.widgets[drop_name]['menu'].delete(0, tk.END)
        module = drop_name.split("_")[0]

        if "lmid" in drop_name:
            opts = [x[0] for x in self.lmids[module]]
            #opts = [x[0] + (f" ({x[1]})" if x[1] else '') for x in self.lmids["host"]]
        elif "obj" in drop_name:
            opts = utils.get_keys(self.panel_acts[module])
        elif "act" in drop_name:
            opts = self.panel_acts[module][self.widgets[module + "_obj_str"].get()]

        opts = sorted(opts)

        drop_var = drop_name[:-4] + "str"
        self.widgets[drop_var].set(opts[0])

        for opt in opts:
            self.widgets[drop_name]["menu"].add_command(
                label = opt,
                command = tk._setit(self.widgets[drop_var], opt)
                )

        if len(opts) == 1:
            self.widgets[drop_name].configure(state="disabled")
        else:
            self.widgets[drop_name].configure(state="normal")

    def set_args(self, module):
        self.cmd_args = {}
        lmid = self.widgets[module + "_lmid_str"].get()
        obj = self.widgets[module + "_obj_str"].get()
        act = self.widgets[module + "_act_str"].get()

        if obj: method = getattr(hal.pools[hal.lmobjs[lmid]], act + '_' + obj)
        else: method = getattr(hal.pools[hal.lmobjs[lmid]], act)

        param_pos, params = utils.get_method_params(method)
        frame = module + "_args_panel_tmp"

        self.widgets[frame].destroy()
        self.widgets[frame] = self.create_frame(self.widgets[module + "_args_panel"])
        self.widgets[frame].pack(fill=tk.X, expand=True)

        frame = self.widgets[frame]

        widgets = {}
        for p, v in params.items():
            self.cmd_args[p] = "NaN"
            text = p.capitalize().replace("_", " ") + (" *" if p in param_pos else "")

            for x in ("html", "css", "php"):
                if x in text:
                    text = text.replace(x, x.upper())

            label = self.create_label(frame, text=text)
            label.pack(side=tk.LEFT, padx=[0, 4])

            if v[0] == "str":
                widgets[p + "_var"] = tk.StringVar(frame)
                widgets[p] = ttk.Entry(frame, textvariable = widgets[p + "_var"])

                if v[1] and v[1] != inspect._empty:
                    widgets[p + "_var"].set(v[1])

            elif v[0] == "bool":
                widgets[p + "_var"] = tk.IntVar(frame)
                widgets[p] = ttk.Checkbutton(frame, variable=widgets[p + "_var"])

            elif v[0] == "env":
                widgets[p + "_var"] = tk.StringVar(frame)
                opts = [k for k, v in utils.hosts.envs.items() if isinstance(k, str)]
                widgets[p] = ttk.OptionMenu(frame, widgets[p + "_var"], v[1], *opts)

            elif v[0] == "web_state":
                widgets[p + "_var"] = tk.StringVar(frame)
                opts = [s[1] for s in sorted(utils.webs.states.items(), key = lambda e: e[0])]
                current_state = utils.webs.states.get(hal.pools.get(hal.lmobjs.get(lmid)).prod_state)
                widgets[p] = ttk.OptionMenu(frame, widgets[p + "_var"], current_state, *opts)

            widgets[p].pack(side=tk.LEFT, padx=[0, 8])

        self.arg_widgets = widgets

    def send_cmd(self, module):
        name = self.widgets[f"{module}_lmid_str"].get()
        act = self.widgets[f"{module}_act_str"].get()
        obj = self.widgets[f"{module}_obj_str"].get()
        args = []

        for arg in self.cmd_args:
            value = self.arg_widgets[arg + "_var"].get()
            if " " in str(value): value = '"' + value + '"'
            if arg == "new_state" and module == "web":
                args.append(f"--new_state={utils.reverse_dict(utils.webs.states)[value]}")
            else:
                args.append(f"--{arg}={value}")

        args = ' '.join(args)

        if obj:
            command = ' '.join([name, act, obj, args])
            cli.process(command)
        else:
            command = ' '.join([name, act, args])
            cli.process(command)

        print(command)

    ## HOSTS

    def set_host_details(self, *args):
        lmid = self.widgets["host_lmid_str"].get()
        if lmid:
            pool = hal.pools[hal.lmobjs[lmid]]
        else:
            pool = hal.pools[hal.host_dbid]

        self.widgets["host_id_str"].set(pool.lmid)
        self.widgets["host_net_str"].set(hal.lmobjs.get(pool.net_id, ["NaN"])[0])
        self.widgets["host_mac_str"].set(pool.mac.upper())
        self.widgets["host_ip_str"].set(pool.ip)
        self.widgets["host_env_str"].set(pool.env)

        self.widgets["host_alias_str"].set(pool.alias if pool.alias else "NaN")
        self.widgets["host_ssh_str"].set(pool.ssh_port if pool.ssh_port != -1 else "NaN")
        self.widgets["host_pg_str"].set(pool.pg_port if pool.pg_port != -1 else "NaN")
        self.widgets["host_pm_str"].set(hal.lmobjs.get(pool.pm_id, ["NaN"])[0])

    def send_host_cmd(self, *args):
        self.send_cmd("host")

    # Dropdowns
    def set_host_lmids(self, *args):
        self.set_dropdown("host_lmid_menu")

    def set_host_objs(self, *args):
        self.set_dropdown("host_obj_menu")

    def set_host_acts(self, *args):
        self.set_dropdown("host_act_menu")

    def set_host_args(self, *args):
        self.set_args("host")


    ## WEBS

    def set_web_details(self, *args):
        lmid = self.widgets["web_lmid_str"].get()
        pool = hal.pools[hal.lmobjs[lmid]]

        try: dssl_date = utils.format_date(pool.dev_ssl_due, "%d %b %Y")
        except: dssl_date = "NaN"

        try: pssl_date = utils.format_date(pool.prod_ssl_due, "%d %b %Y")
        except: pssl_date = "NaN"

        self.widgets["web_id_str"].set(pool.lmid)
        self.widgets["web_ddomain_str"].set(f"{pool.dev_domain}:{pool.dev_port}")
        self.widgets["web_pdomain_str"].set(f"{pool.prod_domain}:{pool.prod_port}")
        self.widgets["web_dlang_str"].set(pool.default_lang)
        self.widgets["web_dtheme_str"].set(pool.default_theme)

        self.widgets["web_alias_str"].set(pool.alias)
        self.widgets["web_dssl_str"].set(dssl_date)
        self.widgets["web_pssl_str"].set(pssl_date)
        self.widgets["web_langs_str"].set(', '.join([utils.projects.langs[l] for l in pool.lang_ids]))
        self.widgets["web_themes_str"].set(', '.join(pool.themes))

    def send_web_cmd(self, *args):
        self.send_cmd("web")

    # Dropdowns
    def set_web_lmids(self, *args):
        self.set_dropdown("web_lmid_menu")

    def set_web_objs(self, *args):
        self.set_dropdown("web_obj_menu")

    def set_web_acts(self, *args):
        self.set_dropdown("web_act_menu")

    def set_web_args(self, *args):
        self.set_args("web")

    ## HISTORY

    def history_up(self, event):
        self.history_index -= 1
        if abs(self.history_index) <= len(cli.history):
            self.widgets["mcmd_input_str"].set(cli.history[self.history_index])
            self.widgets["mcmd_input"].icursor("end")
        else:
            self.history_index += 1

    def history_down(self, event):
        self.history_index += 1
        if self.history_index < 0:
            self.widgets["mcmd_input_str"].set(cli.history[self.history_index])
            self.widgets["mcmd_input"].icursor("end")
        elif self.history_index == 0:
            self.widgets["mcmd_input_str"].set("")
        else:
            self.history_index -= 1


    # STATUS

    def reset_status(self):
        if self.last_timer + timedelta(seconds=10) <= datetime.now():
            self.widgets["status_lvl_str"].set("")
            self.widgets["status_msg_str"].set("")

    def set_status(self, level, color, message):
        self.widgets["status_lvl_str"].set(level)
        self.widgets["status_lvl"].config(foreground = self.colors[color])
        self.widgets["status_msg_str"].set(message)

        if not message.endswith("..."):
            self.widgets["status_lvl"].after(10000, self.reset_status)
            self.last_timer = datetime.now()


    # MAIN

    def start(self):
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

gui = None

def main():
    global gui
    cl = sys.argv[1:]
    hal.start()

    cli.load_history()
    if cl:
        cli.process(' '.join(cl))
    else:
        gui = GUI()
        gui.start()

if __name__ == "__main__":
    lib_path = utils.projects_dir + "venv/lib/"
    packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
    sys.path.append(packages_path)

    import psycopg2, netifaces, requests, sass, markdown
    from ruamel import yaml

    yaml.constructor.SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', utils.webs.construct_yaml_map)

    main()