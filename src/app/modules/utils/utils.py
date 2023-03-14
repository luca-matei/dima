import sys, os, getpass, inspect, subprocess, string, pprint, ast, json, secrets, re, random, ipaddress, crypt
from datetime import datetime

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

    def now(self):
        # https://miro.medium.com/max/2138/1*O7E2cZsFohFNj_oGEe-dYg.png
        return datetime.now().strftime("%d %b, %H:%M:%S")

    def read(self, path, lines=False, host=None, quiet=False):
        is_ast = path.endswith('.ast')
        is_json = path.endswith('.json')

        if path.startswith("/etc/"): root = True
        else: root = False

        contents = no_logs_cmd(f"{'sudo ' if root else ''}cat {path}", catch=True, host=host)

        if f"cat: {path}: No such file or directory" in contents:
            if not quiet:
                try:
                    log(f"'{path}' doesn't exist!", level=4, console=True)
                except:
                    print(f"Error: '{path}' doesn't exist!")

            if lines: return []
            else: return ""

        if is_ast:
            return ast.literal_eval(contents)

        elif is_json:
            if contents: return json.loads(contents)
            else: return ""

        elif lines:
            return [x+'\n' for x in contents.split('\n')]

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

                if int(spaces) == spaces: odd = 0
                else: odd = 1
                spaces = int(spaces)

                table_row += "|" + spaces*' ' + field + spaces*' ' + odd*' '
            table_row += "|"
            table.append(table_row)
        table.append(row_sep)

        return '\n'.join(table)

    def isfile(self, path, host=None, quiet=False):
        response = cmd(f"ls {path}", catch=True, host=host)
        if response == path:
            return 1
        elif "No such file or directory" in response:
            if not quiet:
                log(f"'{path}' doesn't exist!", level=3, console=True)
            return 0
        return 1

    def replace_multiple(self, text:'str', reps:'dict'):
        # Reps = Replacements
        reps_sorted = sorted(reps, key=len, reverse=True)
        reps_escaped = map(re.escape, reps_sorted)
        pattern = re.compile("|".join(reps_escaped))

        return pattern.sub(lambda match: reps[match.group(0)], text)

    def format_tpl(self, tpl:'str', keys:'dict'):
        tpl = self.read(self.get_src_dir() + "assets/tpls/" + tpl) if tpl.endswith(".tpl") else tpl

        reps = {"%" + k.upper() + "%": v for k, v in keys.items()}
        return self.replace_multiple(tpl, reps)

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

    def join_modules(self, modules, module_path, file_path, module_host=None, file_host=None):
        mammoth = [self.read(module_path + m, host=module_host) for m in modules]
        self.write(file_path, "\n\n".join(mammoth), host=file_host)

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

            # Solve properties
            if properties != None:
                for prop in properties:
                    if prop[0] in self.html_tags + tags:
                        box_html += solve_box(prop)

                    elif prop[0] == "text":
                        if type(prop[1]) == list:
                            texts = dict(prop[1])
                            text = texts.get(lang, texts.get(default_lang))

                            if tag not in ("a", "i", "button", "span", "h1", "h2", "h3", "h4", "h5", "h6"):
                                text = self.md2html(text)

                        else:
                            text = prop[1]

                        text = text.replace("\\", "<br>")

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
                    tag_html.append(f"""<h6><span>{f_text}</span>{f_required}<span class=\"grow\"></span><a href="docs/forms#{attrs.get('type')}"><i class=\"fa fa-circle-info\"></i></a></h6>""")

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
