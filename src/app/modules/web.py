class Web(Project):
    def __init__(self, dbid):
        Project.__init__(self, dbid)

        query = "select a.name, b.port, b.modules, b.langs, b.themes, b.default_lang, b.default_theme, b.has_animations from domains a, web.webs b where b.domain=a.id and b.lmobj=%s;"
        params = dbid,
        self.domain, self.port, self.module_ids, self.lang_ids, self.theme_ids, self.default_lang_id, self.default_theme_id, self.has_animations = hal.db.execute(query, params)[0]

        self.dev_domain = "dev." + self.domain
        self.modules = [utils.webs.modules[m] for m in self.module_ids]
        self.langs = [utils.projects.langs[l] for l in self.lang_ids]
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

    def build(self):
        log(f"Building {self.lmid} ...", console=True)
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

        for node in dir_tree:
            node = self.repo_dir + node
            if not utils.isfile(node, host=self.dev_host):
                if node.endswith('/'):
                    cmd(f"mkdir " + node, host=self.dev_host)
                else:
                    cmd(f"touch " + node, host=self.dev_host)

        has_db = cmd(utils.dbs.query.format(f"select 1 from pg_database where datname='{self.lmid}';"), catch=True)
        if not has_db:
            hal.pools.get(self.dev_host_id).create_pg_role(self.lmid)
            hal.pools.get(self.dev_host_id).create_pg_db(self.lmid)

        self.generate_ssl()
        self.default()
        hal.pools.get(hal.host_dbid).update_hosts_file()

    def default(self, yes:'bool'=False):
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format {self.name}?")
            if not yes:
                log("Aborted.", console=True)
                return

        log(f"Setting {self.dev_domain} to 'Hello World' ...", console=True)

        settings = {
            "lmid": self.lmid,
            "domain": self.domain,
            "log_level": 2,
            "default_lang": self.default_lang,
            "default_theme": self.default_theme,
            }

        utils.write(self.app_dir + "settings.ast", settings, host=self.dev_host)

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

        self.update_py()
        self.default_html(True)
        self.config()
        self.update_css()

    def default_html(self, yes:'bool'=False, hello:'bool'=False):
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format {self.name} HTML?")
            if not yes:
                log("Aborted.", console=True)
                return

        if hello:
            log(f"Setting {self.dev_domain} html to 'Hello World' ...", console=True)
            cmd(f"rm -r {self.app_dir}html/", host=self.dev_host)
            hal.pools.get(self.dev_host_id).send_file(utils.src_dir + "assets/web/app/html/", self.app_dir + "html/")
        else:
            log(f"Updating structure html for {self.dev_domain} ...", console=True)
            cmd(f"rm -r {self.app_dir}html/*.yml", host=self.dev_host)
            hal.pools.get(self.dev_host_id).send_file(utils.src_dir + "assets/web/app/html/*.yml", self.app_dir + "html/")

        self.update_html()
        self.restart()

    def default_js(self, yes:'bool'=False):
        if not yes:
            yes = utils.yes_no(f"Are you sure you want to format {self.name} JS?")
            if not yes:
                log("Aborted.", console=True)
                return

        log(f"Setting {self.dev_domain} JS to 'Hello World' ...", console=True)

        cmd(f"rm -r {self.repo_dir}src/assets/js/", host=self.dev_host)
        # RENAME CLASSES
        hal.pools.get(self.dev_host_id).send_file(utils.src_dir + "assets/web/assets/js/", self.repo_dir + "src/assets/js/")

    def update_html(self):
        log(f"Updating html for {self.dev_domain} ...", console=True)

        self.db.erase()
        self.db.build()

        query = f"insert into methods (name) values {', '.join(['(%s)' for m in utils.webs.methods])} returning id, name;"
        params = utils.webs.methods
        methods = dict(self.db.execute(query, params))
        methods.update(utils.reverse_dict(methods))

        query = f"insert into langs (code) values {', '.join(['(%s)' for l in self.langs])} returning id, code;"
        params = self.langs
        langs = dict(self.db.execute(query, params))
        langs.update(utils.reverse_dict(langs))

        query = f"insert into modules (name) values {', '.join(['(%s)' for m in self.modules])} returning id, name;"
        params = self.modules
        modules = dict(self.db.execute(query, params))
        modules.update(utils.reverse_dict(modules))

        app_wrapper = "<!doctype html>" + YML2HTML(utils.read(self.html_dir + "wrapper.yml", host=self.dev_host), self.default_lang, self.default_lang).html
        top_button = YML2HTML(utils.read(self.html_dir + "top-button.yml", host=self.dev_host), self.default_lang, self.default_lang).html

        query = "insert into fractions (name, lang, html) values (%s, %s, %s);"
        for lang in self.langs:
            user_drop_html = YML2HTML(utils.read(self.html_dir + "user-drop.yml", host=self.dev_host), self.default_lang, lang).html
            params = "user-drop", langs[lang], user_drop_html
            self.db.execute(query, params)

            if len(self.langs) == 1:
                lang_selector = ""

            elif len(self.langs) == 2:
                if self.langs[0] == self.default_lang: other_lang = self.langs[1]
                else: other_lang = self.langs[0]

                if lang == self.langs[0]: to_lang = self.langs[1]
                else: to_lang = self.langs[0]

                lang_selector = YML2HTML(utils.read(self.html_dir + "lang-switch.yml", host=self.dev_host), self.default_lang, lang).html
                lang_selector = utils.format_tpl(lang_selector, {
                    "default_lang": self.default_lang.upper(),
                    "to_lang": to_lang,
                    "other_lang": other_lang.upper(),
                    })

            else:
                lang_selector = YML2HTML(utils.read(self.html_dir + "lang-drop.yml", host=self.dev_host), self.default_lang, lang).html

            if len(self.themes) == 1:
                theme_selector = ""

            elif len(self.themes) == 2:
                theme_selector = YML2HTML(utils.read(self.html_dir + "theme-switch.yml", host=self.dev_host), self.default_lang, lang).html

            else:
                theme_selector = YML2HTML(utils.read(self.html_dir + "theme-drop.yml", host=self.dev_host), self.default_lang, lang).html

            guest_drop_html = YML2HTML(utils.read(self.html_dir + "guest-drop.yml", host=self.dev_host), self.default_lang, lang).html
            params = "guest-drop", langs[lang], utils.format_tpl(guest_drop_html, {
                "lang_selector": lang_selector,
                "theme_selector": theme_selector,
                })
            self.db.execute(query, params)

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
                for lang in self.langs:
                    body = YML2HTML(yml, self.default_lang, lang).html
                    app_header = YML2HTML(utils.read(f"{self.html_dir}app-header.yml", host=self.dev_host), self.default_lang, lang).html
                    app_footer = YML2HTML(utils.read(f"{self.html_dir}app-footer.yml", host=self.dev_host), self.default_lang, lang).html
                    cookies_notice = YML2HTML(utils.read(f"{self.html_dir}cookies-notice.yml", host=self.dev_host), self.default_lang, lang).html

                    title = meta["title"].get(lang, meta["title"][self.default_lang])
                    # FORMAT TITLE
                    #if self.has_domain_in_title:
                        #title += " | " + self.domain

                    description = meta["description"].get(lang, meta["description"][self.default_lang])
                    permalink = ""
                    og_url = ""
                    og_image = ""
                    alt = ''.join([f'<link rel="alternate" href="/{l}/{permalink}" hreflang="{l}"' for l in self.langs if l != lang])

                    html = utils.format_tpl(app_wrapper, {
                        "lang": lang,
                        "default_theme": str(self.default_theme_id),
                        "alt": alt,
                        "name": self.name,
                        "title": title,
                        "description": description,
                        "og_url": og_url,
                        "og_image": og_image,
                        "app_header": app_header,
                        "domain": self.domain,
                        "aside": "",
                        "body": body,
                        "app_footer": app_footer,
                        "copyright_year": datetime.now().year,
                        "copyright_name": '.'.join(self.domain.split(".")[-2:]),
                        "top_button": top_button,
                        "cookies_notice": cookies_notice,
                        "permalink": permalink,
                        })

                    query = "insert into pages (name, module, section, method, lang, first, html) values (%s, %s, %s, %s, %s, %s, %s);"
                    params = name, modules[meta["module"]], section_id, methods[method], langs[lang], first, html,
                    self.db.execute(query, params)

            for section in utils.get_dirs(section_dir, self.dev_host):
                solve_section(section_dir + section + '/', section, section_id)

        for section in utils.get_dirs(self.html_dir, self.dev_host):
            solve_section(self.html_dir + section + '/', section, 0)

    def update_py(self):
        # Joins .py files from main host and sends the result on the remote host
        log(f"Updating source code for {self.name} ...", console=True)
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
        # Joins CSS files from main host and sends the result on the remote host
        log(f"Updating CSS for {self.name} ...", console=True)

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

        css = sass.compile(string=utils.read(scss_file), output_style='compressed')
        # RENAME CLASSES
        utils.write(self.repo_dir + "src/assets/css/app.css", css, host=self.dev_host)

    def generate_ssl(self):
        if not utils.isfile(self.dev_ssl_dir, host=self.dev_host):
            cmd("mkdir " + self.dev_ssl_dir, host=self.dev_host)

        # Production certificates
        #log(f"Generating Let's Encrypt SSL certs for {self.dev_domain}. This may take a while ...", console=True)

        log(f"Generating self-signed SSL certs for {self.dev_domain}. This may take a while ...", console=True)
        cmd(f'sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout {self.dev_ssl_dir}privkey.pem -out {self.dev_ssl_dir}pubkey.pem -subj "/C=RO/ST=Bucharest/L=Bucharest/O={hal.domain}/CN={self.dev_domain}"', host=self.dev_host)

        query = "update web.webs set ssl_last_gen=%s where lmobj=%s;"
        params = datetime.now(), self.dbid,
        hal.db.execute(query, params)

    def config_uwsgi(self):
        log(f"Configuring uWSGI for {self.dev_domain} ...", console=True)
        uwsgi_config = utils.format_tpl("web/app/uwsgi.tpl", {
            "port": str(self.port),
            "app_dir": self.app_dir,
            "projects_dir": utils.projects_dir,
            "lmid": self.lmid,
            "log_file": self.log_file,
            })
        utils.write(self.app_dir + "uwsgi.ini", uwsgi_config, host=self.dev_host)
        self.restart()

    def config_supervisor(self):
        log(f"Configuring Supervisor for {self.name} ...", console=True)
        supervisor_config = utils.format_tpl("web/app/supervisor.tpl", {
            "lmid": self.lmid,
            "projects_dir": utils.projects_dir,
            "app_dir": self.app_dir,
            })
        utils.write(f"/etc/supervisor/conf.d/{self.lmid}.conf", supervisor_config, host=self.dev_host)
        hal.pools.get(self.dev_host_id).restart_supervisor()

    def config_nginx(self):
        log(f"Configuring Nginx for {self.dev_domain} ...", console=True)
        manual = self.app_dir + "manual/nginx.tpl"
        if utils.isfile(manual, host=self.dev_host):
            tpl = utils.read(manual, host=self.dev_host)
        else:
            tpl = "web/app/nginx.tpl"

        nginx_config = utils.format_tpl(tpl, {
            "domain": self.dev_domain,
            "ssl_dir": self.dev_ssl_dir,
            "hal_ssl_dir": utils.ssl_dir,
            "ocsp": "off", # Check environment, 'on' for production
            "res_dir": utils.res_dir,
            "repo_dir": self.repo_dir,
            "port": self.port,
            "lmid": self.lmid
            })
        utils.write(f"/etc/nginx/sites-enabled/{self.lmid}", nginx_config, host=self.dev_host)
        hal.pools.get(self.dev_host_id).restart_nginx()

    def config(self):
        self.config_uwsgi()
        self.config_supervisor()
        self.config_nginx()

    def restart(self):
        log(f"Restarting {self.dev_domain} ...", console=True)
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;", host=self.dev_host)
        cmd(f"sudo supervisorctl restart {self.lmid}", host=self.dev_host)
