class Web(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

        query = "select a.name, b.port, b.modules, b.langs, b.themes, b.default_lang, b.default_theme, b.has_animations from domains a, web.webs b where b.domain=a.id and b.lmobj=%s;"
        params = dbid,
        self.domain, self.port, self.module_ids, self.lang_ids, self.theme_ids, self.default_lang_id, self.default_theme_id, self.has_animations = hal.db.execute(query, params)[0]

        self.global_html = {}
        self.css_classes = {}
        self.dev_domain = "dev." + self.domain
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

        self.ssl_dir = utils.ssl_dir + self.domain + '/'
        self.dev_ssl_dir = utils.ssl_dir + self.dev_domain + '/'
        self.app_dir = self.repo_dir + "src/app/"
        self.html_dir = self.app_dir + "html/"

        # Assign a process port
        if not self.port:
            self.port = hal.pools.get(self.dev_host_id).next_port()
            query = "update web.webs set port=%s where lmobj=%s;"
            params = self.port, self.dbid,
            hal.db.execute(query, params)
            self.config()

        if not utils.isfile(self.log_file, host=self.dev_host):
            cmd(f"touch {self.log_file}", host=self.dev_host)
            cmd(f"sudo chown www-data:www-data {self.log_file}", host=self.dev_host)

        if not utils.isfile(self.app_dir + "db/db_pass", host=self.dev_host):
            self.build()

        self.db = Db(self.lmid, self.dbid, self.dev_host)

        # Fix for other projects
        if self.lmid == "lm7":
            self.update_css()  # Bcs I'm not saving the translates

    def build(self):
        """
            Command only for dev environment.
        """
        log(f"Building '{self.name}' ...", console=True)
        dir_tree = (
            "docs/",
            "src/",
                "src/app/",
                    "src/app/db/",
                    "src/app/html/",
                "src/assets/",
                    "src/assets/icons/",
                    "src/assets/fonts/",
                    "src/assets/img/",
                    "src/assets/css/",
                    "src/assets/js/",
            "LICENSE",
            "README.md",
            )

        utils.create_dir_tree(dir_tree, root=self.repo_dir, host=self.dev_host)
        self.create_db()
        self.generate_ssl()
        self.default(yes=True)
        hal.pools.get(hal.host_dbid).update_hosts_file()

    def create_db(self, env:'env'="dev"):
        host = getattr(self, env + "_host")
        host_id = getattr(self, env + "_host_id")
        hal.pools.get(host_id).create_pg_role(self.lmid)
        hal.pools.get(host_id).create_pg_db(self.lmid)

    def default(self, yes:'bool'=False):
        """
            Command only for dev environment.
        """
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format '{self.name}'?")
            if not yes:
                log("Aborted.", console=True)
                return

        log(f"Setting '{self.name}' to 'Hello World' ...", console=True)

        settings = {
            "lmid": self.lmid,
            "domain": self.domain,
            "log_level": 2,
            "default_lang": self.default_lang,
            "default_theme": self.default_theme,
            }

        utils.write(self.app_dir + "settings.ast", settings, host=self.dev_host)
        self.default_db(yes=True)
        self.update_py()
        self.default_html(yes=True, hello=True)
        self.config()
        self.update_css()
        self.default_js(True)

    def default_db(self, yes:'bool'=False):
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format '{self.name}' database?")
            if not yes:
                log("Aborted.", console=True)
                return

        host_struct_file = utils.src_dir + "assets/web/app/db/struct.ast"
        remote_struct_file = self.app_dir + "db/struct.ast"
        host_default_file = utils.src_dir + "assets/web/app/db/default.ast"
        remote_default_file = self.app_dir + "db/default.ast"

        if self.dev_host_id == hal.host_dbid:
            utils.copy(host_struct_file, remote_struct_file)
            utils.copy(host_default_file, remote_default_file)
        else:
            hal.pools.get(self.dev_host_id).send_file(host_struct_file, remote_struct_file)
            hal.pools.get(self.dev_host_id).send_file(host_default_file, remote_default_file)

        self.db.rebuild()

        query = f"insert into methods (name) values {', '.join(['(%s)' for m in utils.webs.methods])};"
        params = utils.webs.methods
        self.db.execute(query, params)

        langs = [v for k, v in self.langs.items() if type(v)==str]
        query = f"insert into langs (code) values {', '.join(['(%s)' for l in langs])};"
        params = langs
        self.db.execute(query, params)

        modules = [v for k, v in self.modules.items() if type(v)==str]
        query = f"insert into modules (name) values {', '.join(['(%s)' for m in modules])};"
        params = modules
        self.db.execute(query, params)

    def default_html(self, yes:'bool'=False, hello:'bool'=False):
        """
            Command only for dev environment.
        """
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format '{self.name}' HTML?")
            if not yes:
                log("Aborted.", console=True)
                return

        src_html = utils.src_dir + "assets/web/app/html/"
        dest_html = self.app_dir + "html/"

        if hello:
            log(f"Setting '{self.name}' HTML to 'Hello World' ...", console=True)
            cmd(f"rm -r {self.app_dir}html/", host=self.dev_host)
            if self.dev_host_id == hal.host_dbid:
                utils.copy(src_html, dest_html)
            else:
                hal.pools.get(self.dev_host_id).send_file(src_html, dest_html)
        else:
            # WARNING: THIS ONLY DELETES THE FILES, IT DOESN'T COPY
            log(f"Updating structure HTML for '{self.name}' ...", console=True)
            cmd(f"rm -r {self.app_dir}html/*.yml", host=self.dev_host)
            if self.dev_host_id == hal.host_dbid:
                utils.copy(src_html + "*.yml", dest_html)
            else:
                hal.pools.get(self.dev_host_id).send_file(dest_html + "*.yml", dest_html)

        self.update_html()
        self.restart()

    def default_js(self, yes:'bool'=False):
        """
            Command only for dev environment.
        """
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format {self.name} JS?")
            if not yes:
                log("Aborted.", console=True)
                return

        log(f"Setting '{self.name}' JS to 'Hello World' ...", console=True)

        cmd(f"rm {self.repo_dir}src/assets/js/*.js", host=self.dev_host)
        src_js_dir = utils.src_dir + "assets/web/assets/js/"
        for script in utils.get_files(src_js_dir):
            utils.write(
                self.repo_dir + "src/assets/js/" + script,
                utils.replace_multiple(utils.read(src_js_dir + script), self.css_classes),
                host=self.dev_host
                )

    def update_js(self):
        self.default_js(yes=True)

    def yml2html(self, yml, lang):
        if yml.endswith(".yml"): yml = self.html_dir + yml
        return utils.yml2html(yml, lang, self.default_lang, self.global_html, self.dev_host)

    def update_global_html(self):
        log(f"Updating global html for '{self.name}' ...", console=True)

        var_files = utils.get_files(self.html_dir + "_fractions/*.yml", host=self.dev_host)
        query = "insert into fractions (name, lang, html) values (%s, %s, %s);"

        # Update global and variables html
        langs = [v for k, v in self.langs.items() if type(v)==str]
        for lang in langs:
            if not self.global_html.get(lang):
                self.global_html[lang] = {}

            for var_file in var_files:
                self.global_html[lang][var_file[:-4]] = self.yml2html("_fractions/" + var_file, lang)

            # Save logged user dropdown
            user_drop_html = utils.replace_multiple(self.yml2html("user-drop.yml", lang), self.css_classes)
            params = "user-drop", self.langs[lang], user_drop_html
            self.db.execute(query, params)

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
            guest_drop_html = utils.replace_multiple(guest_drop_html, self.css_classes)
            params = "guest-drop", self.langs[lang], guest_drop_html,
            self.db.execute(query, params)

            for h in ("app-wrapper", "app-header", "app-footer", "cookies-notice", "hide-all", "top-button"):
                self.global_html[lang][h] = self.yml2html(h + ".yml", lang)

            self.global_html[lang]["app-wrapper"] = "<!doctype html>" + self.global_html[lang]["app-wrapper"]

    def update_html(self, section:'str'= "", global_html:'bool'=False):
        """
            Command only for dev environment.
        """
        log(f"Updating html for '{self.name}' ...", console=True)

        method_ids = dict(self.db.execute("select name, id from methods;"))

        # Erase current html
        self.db.format_table("sections")
        self.db.format_table("pages")

        section_dirs = utils.get_dirs(self.html_dir, self.dev_host)
        section_dirs.remove("_fractions")

        if global_html:
            self.db.format_table("fractions")
            self.update_global_html()

        langs = [v for k, v in self.langs.items() if type(v)==str]
        def solve_section(section_dir, section_name, parent_id):
            query = "insert into sections (name, parent) values (%s, %s) returning id;"
            params = section_name, parent_id
            section_id = self.db.execute(query, params)[0][0]

            pages = utils.get_files(section_dir + "*.yml", host=self.dev_host)
            for page in pages:
                filename = page.split(".")[0].split("-")
                name, method = filename[:2]
                first = len(filename) == 3

                if name == "lm_wrapper":
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
                    if meta["wrapper"]:
                        # Save wrappers under meta["wrapper"]
                        body = self.yml2html(f"{meta['wrapper']}-{method}.yml", lang).replace("%CONTENT%", body)

                    # FORMAT TITLE
                    #if self.has_domain_in_title:
                        #title += " | " + self.domain

                    description = meta["description"].get(lang, meta["description"][self.default_lang])
                    og_url = ""
                    og_image = ""
                    alt = ''.join([f'<link rel="alternate" href="/{l}/%PERMALINK%" hreflang="{l}"' for l in langs if l != lang])

                    html = utils.format_tpl(self.global_html[lang]["app-wrapper"], {
                        "lang": lang,
                        "default_theme": str(self.default_theme_id),
                        "alt": alt,
                        "name": self.name,
                        "title": title,
                        "description": description,
                        "og_url": og_url,
                        "og_image": og_image,
                        "hide_all": self.global_html[lang]["hide-all"],
                        "app_header": self.global_html[lang]["app-header"],
                        "domain": self.domain,
                        "aside": "",
                        "body": body,
                        "app_footer": self.global_html[lang]["app-footer"],
                        "copyright_year": datetime.now().year,
                        "copyright_name": '.'.join(self.domain.split(".")[-2:]),
                        "top_button": self.global_html[lang]["top-button"],
                        "cookies_notice": self.global_html[lang]["cookies-notice"],
                        })

                    # Replace reusable components
                    html_vars = re.findall("%VAR-([^%]*)%", html)
                    reps = {f"%VAR-{k}%": self.global_html[lang].get(k.lower(), "NONE") for k in html_vars}

                    # Rename CSS classes
                    reps.update(self.css_classes)

                    html = utils.replace_multiple(html, reps)

                    query = "insert into pages (name, module, section, method, lang, first, html) values (%s, %s, %s, %s, %s, %s, %s);"
                    params = name, self.modules[meta["module"]], section_id, method_ids[method], self.langs[lang], first, html,
                    self.db.execute(query, params)

            for section in utils.get_dirs(section_dir, self.dev_host):
                solve_section(section_dir + section + '/', section, section_id)

        for section in section_dirs:
            solve_section(self.html_dir + section + '/', section, 0)

        self.restart()

    def update_py(self):
        """
            Command only for dev environment.
        """
        # Joins .py files from main host and sends the result on the remote host
        log(f"Updating source code for '{self.name}' ...", console=True)
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
            file_host = self.dev_host)

        self.restart()

    def update_css(self):
        """
            Command only for dev environment.
            Joins CSS files from main host and sends the result on the remote host
        """
        log(f"Updating CSS for '{self.name}' ...", console=True)

        def rename_classes():
            for i in range(len(classes)):
                yield ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(8))

        scss_file = utils.tmp_dir + "css.scss"
        utils.join_modules((
            "palettes.scss",
            "document.scss",
            "structure.scss",
            "text.scss",
            "spacing.scss",
            "objects.scss",
            "forms.scss",
            "animations.scss",
            "media.scss",
            ),
            module_path = utils.src_dir + "assets/web/assets/css/",
            file_path = scss_file)

        try:
            css = sass.compile(string=utils.read(scss_file), output_style='compressed')
        except Exception as e:
            log("Couldn't compile Sass! Exception:\n\n" + e, level=4, console=True)
            return

        self.css_classes = {}
        classes = re.findall("[#\.][_a-zA-Z]+[_a-zA-Z0-9-]*[:\w\s]*\{", css)
        new_classes = rename_classes()

        for c in classes:
            if not c.startswith(".fa"):
                c_name = c.split(' ')[0].split(":")[0][1:].replace("{", "")
                print(c_name)
                self.css_classes[c_name] = next(new_classes)

        utils.write(
            self.repo_dir + "src/assets/css/app.css",
            utils.replace_multiple(css, self.css_classes),
            host=self.dev_host
            )

        self.update_js()
        self.update_global_html()
        self.update_html()

    def generate_ssl(self):
        if not utils.isfile(self.dev_ssl_dir, host=self.dev_host):
            cmd("mkdir " + self.dev_ssl_dir, host=self.dev_host)

        # Production certificates
        #log(f"Generating Let's Encrypt SSL certs for {self.dev_domain}. This may take a while ...", console=True)

        log(f"Generating self-signed SSL certs for '{self.name}'. This may take a while ...", console=True)
        cmd(f'sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout {self.dev_ssl_dir}privkey.pem -out {self.dev_ssl_dir}pubkey.pem -subj "/C=RO/ST=Bucharest/L=Bucharest/O={hal.domain}/CN={self.dev_domain}"', host=self.dev_host)

        query = "update web.webs set ssl_last_gen=%s where lmobj=%s;"
        params = datetime.now(), self.dbid,
        hal.db.execute(query, params)

    def config_uwsgi(self, env:'env'="dev"):
        log(f"Configuring uWSGI for '{self.name}' ({env}) ...", console=True)
        host = getattr(self, env + "_host")

        uwsgi_config = utils.format_tpl("web/app/uwsgi.tpl", {
            "port": str(self.port),
            "app_dir": self.app_dir,
            "projects_dir": utils.projects_dir,
            "lmid": self.lmid,
            "log_file": self.log_file,
            })
        utils.write(self.app_dir + "uwsgi.ini", uwsgi_config, host=host)

        self.restart(env)

    def config_supervisor(self, env:'env'="dev"):
        log(f"Configuring Supervisor for '{self.name}' ({env}) ...", console=True)
        host = getattr(self, env + "_host")
        host_id = getattr(self, env + "_host_id")

        supervisor_config = utils.format_tpl("web/app/supervisor.tpl", {
            "lmid": self.lmid,
            "projects_dir": utils.projects_dir,
            "app_dir": self.app_dir,
            })
        utils.write(f"/etc/supervisor/conf.d/{self.lmid}.conf", supervisor_config, host=host)

        hal.pools.get(host_id).restart_supervisor()

    def config_nginx(self, env:'env'="dev"):
        log(f"Configuring Nginx for '{self.name}' ({env}) ...", console=True)
        host = getattr(self, env + "_host")
        host_id = getattr(self, env + "_host_id")

        if env == "dev":
            domain = self.dev_domain
            ssl_dir = self.dev_ssl_dir
        else:
            domain = self.domain
            ssl_dir = self.ssl_dir

        manual = self.app_dir + "manual/nginx.tpl"
        if utils.isfile(manual, host=host, quiet=True):
            tpl = utils.read(manual, host=host)
        else:
            tpl = "web/app/nginx.tpl"

        nginx_config = utils.format_tpl(tpl, {
            "domain": domain,
            "ssl_dir": ssl_dir,
            "hal_ssl_dir": utils.ssl_dir,
            "ocsp": "off", # Check environment, 'on' for production
            "projects_dir": utils.projects_dir,
            "res_dir": utils.res_dir,
            "repo_dir": self.repo_dir,
            "port": self.port,
            "lmid": self.lmid
            })
        utils.write(f"/etc/nginx/sites-enabled/{self.lmid}", nginx_config, host=host)
        hal.pools.get(host_id).restart_nginx()

    def config(self, env:'env'="dev"):
        self.config_uwsgi(env)
        self.config_supervisor(env)
        self.config_nginx(env)

    def restart(self, env:'env'="dev"):
        log(f"Restarting '{self.name}' ({env}) ...", console=True)
        host = getattr(self, env + "_host")
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;", host=host)
        cmd(f"sudo supervisorctl restart {self.lmid}", host=host)
