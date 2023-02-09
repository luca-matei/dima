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

        has_db = cmd(utils.dbs.query.format(f"select 1 from pg_database where datname='{self.lmid}';"), catch=True)
        if not has_db:
            hal.pools.get(self.dev_host_id).create_pg_role(self.lmid)
            hal.pools.get(self.dev_host_id).create_pg_db(self.lmid)

        self.generate_ssl()
        self.default()

    def default(self):
        yes = utils.yes_no(f"Are you sure you want to format {self.name}?")
        if not yes:
            log("Aborted.", console=True)
            return

        log(f"Setting {self.dev_domain} to 'Hello World' ...", console=True)

        modules = (
            "utils/utils.py",
            "app.py",
            "logs.py",
            "db.py",
            "html.py",
            "http.py",
            "process.py",
            "request.py",
            "response.py",
            "main.py",
            )

        utils.write(self.app_dir + "app.py", "", host=self.dev_host)

        for module in modules:
            utils.write(self.app_dir + "app.py", utils.read(utils.src_dir + "assets/web/app/modules/" + module) + "\n\n", mode='a', host=self.dev_host)

        settings = {
            "log_level": 2,
            }

        utils.write(self.app_dir + "settings.ast", settings, host=self.dev_host)

        # Replace old html
        cmd(f"rm -r {self.app_dir}html/", host=self.dev_host)
        hal.pools.get(self.dev_host_id).send_file(utils.src_dir + "assets/web/app/html/", self.app_dir + "html/")

        self.update_html()
        self.config()

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

        app_wrapper = utils.read(self.html_dir + "wrapper.html", host=self.dev_host)
        top_button = YML2HTML(utils.read(self.html_dir + "top-button.yml", host=self.dev_host), self.default_lang, self.default_lang).html

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

                meta, yml = utils.read(section_dir + page, host=self.dev_host).split("----")
                meta = yaml.safe_load(meta)
                for lang in self.langs:
                    body = YML2HTML(yml, self.default_lang, lang).html
                    app_header = YML2HTML(utils.read(f"{self.html_dir}app-header.yml", host=self.dev_host), self.default_lang, lang).html
                    app_footer = YML2HTML(utils.read(f"{self.html_dir}app-footer.yml", host=self.dev_host), self.default_lang, lang).html
                    copyright = YML2HTML(utils.read(f"{self.html_dir}copyright.yml", host=self.dev_host), self.default_lang, lang).html
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
                        .replace("%COOKIES_NOTICE", cookies_notice)\
                        .replace("%PERMALINK", permalink)

                    query = "insert into pages (name, module, section, method, lang, first, html) values (%s, %s, %s, %s, %s, %s, %s);"
                    params = name, modules[meta["module"]], section_id, methods[method], langs[lang], first, html,
                    self.db.execute(query, params)

            for section in utils.get_dirs(section_dir, self.dev_host):
                solve_section(section_dir + section + '/', section, section_id)

        for section in utils.get_dirs(self.html_dir, self.dev_host):
            solve_section(self.html_dir + section + '/', section, 0)

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

    def restart(self):
        log(f"Restarting {self.dev_domain} ...", console=True)
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;", host=self.dev_host)
        cmd(f"sudo supervisorctl restart {self.lmid}", host=self.dev_host)

    def config(self):
        self.config_uwsgi()
        self.config_supervisor()
        self.config_nginx()

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
        nginx_config = utils.format_tpl("web/app/nginx.tpl", {
            "domain": self.dev_domain,
            "ssl_dir": self.dev_ssl_dir,
            "hal_ssl_dir": utils.ssl_dir,
            "ocsp": "off", # Check environment, 'on' for production
            "repo_dir": self.repo_dir,
            "port": self.port,
            "lmid": self.lmid
            })
        utils.write(f"/etc/nginx/sites-enabled/{self.lmid}", nginx_config, host=self.dev_host)
        hal.pools.get(self.dev_host_id).reload_nginx()
