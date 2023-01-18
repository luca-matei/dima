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
