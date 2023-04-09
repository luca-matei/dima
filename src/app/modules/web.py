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

    def env_var(self, env, name):
        if name == "db" and env == "dev":
            return getattr(self, name)
        else:
            return getattr(self, env + "_" + name)

    def check(self):
        for env in ("dev", "prod"):
            port = self.env_var(env, "port")
            host_id = self.env_var(env, "host_id")
            host = self.env_var(env, "host")
            domain = self.env_var(env, "domain")

            # Assign a process port
            if not port:
                setattr(self, env + "_port", hal.pools.get(host_id).next_port())
                port = self.env_var(env, "port")

                query = f"update web.webs set {env}_port=%s where lmobj=%s;"
                params = port, self.dbid,
                hal.db.execute(query, params)

                log(f"Assigned {env} port {port} to '{domain}'", console=True)
                self.config(env)

            # Create log files
            if not utils.isfile(self.log_file, host=host):
                cmd(f"touch {self.log_file}", host=host)
                cmd(f"sudo chown www-data:www-data {self.log_file}", host=host)

            if not utils.isfile(self.app_dir + "db/db_pass", host=host):
                self.build(env)

    def yml2html(self, yml, lang):
        if yml.endswith(".yml"): yml = self.html_dir + yml
        return utils.yml2html(yml, lang, self.default_lang, self.global_html, self.dev_host)

    def build(self, env:'env'="dev"):
        """
            Command used when creating the web, when the structure has changed or when parts are missing.
        """
        domain = self.env_var(env, "domain")
        host = self.env_var(env, "host")
        host_id = self.env_var(env, "host_id")

        log(f"Building '{domain}' ...", console=True)

        dir_tree = (
            "src/",
            "src/app/",
                "src/app/db/",
            "src/assets/",
                "src/assets/icons/",
                "src/assets/fonts/",
                "src/assets/img/",
                "src/assets/css/",
                "src/assets/js/",
            )

        if env == "dev":
            dir_tree.extend((
                "docs/",
                "src/app/html/",
                "LICENSE",
                "README.md",
            ))

        utils.create_dir_tree(dir_tree, root=self.repo_dir, host=host)
        self.generate_ssl(env)
        self.default(confirm=True)

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
        if not confirm:
            if not utils.confirm(f"Are you sure you want to format '{self.dev_domain}' HTML?"):
                log("Aborted", console=True)
                return

        src_html = utils.src_dir + "assets/web/app/html/"
        dest_html = self.app_dir + "html/"

        if hello:
            log(f"Setting '{self.dev_domain}' HTML to 'Hello World' ...", console=True)
            cmd(f"rm -r {self.app_dir}html/", host=self.dev_host)
            if self.dev_host_id == hal.host_dbid:
                utils.copy(src_html, dest_html)
            else:
                hal.pools.get(self.dev_host_id).send_file(src_html, dest_html)

            log(f"Set '{self.dev_domain}' HTML to 'Hello World.'", console=True)

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

    def update_global_html(self, env:"env"="dev"):
        domain = self.env_var(env, "domain")
        db = self.env_var(env, "db")

        log(f"Updating Global HTML for '{domain}' ...", console=True)

        self.global_html = {}
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
            css_classes = self.css_classes if env == "prod" else {}
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

                    html = utils.format_tpl(self.global_html[lang]["app-wrapper"], {
                        "title": title,
                        "description": description,
                        "og_url": og_url,
                        "og_image": og_image,
                        "aside": "",
                        "body": body,
                        })

                    # Replace reusable components
                    html_vars = re.findall("%VAR-([^%]*)%", html)
                    reps = {f"%VAR-{k}%": self.global_html[lang].get(k.lower(), "NONE") for k in html_vars}

                    # Rename CSS classes
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
                "media.scss",
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
        params = datetime.now() + datetime.timedelta(3*365/12-3), self.dbid,
        hal.db.execute(query, params)

        log(f"Generated SSL certificates for '{domain}'", console=True)

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
        nginx_file = "/etc/nginx/sites-enabled/{self.lmid}"
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
        if env == "prod" and self.prod_state == 0:
            log("No web app is running on production!", level=4, console=True)
            return

        host = self.env_var(env, "host")
        domain = self.env_var(env, "domain")

        log(f"Restarting '{domain}' ...", console=True)
        # To do: Save log file
        cmd(f"sudo rm /var/log/supervisor/{self.lmid}.err.log;", host=host)
        cmd(f"sudo supervisorctl restart {self.lmid}", host=host)
        log(f"Restarted '{domain}'", console=True)

    def change_state(self, new_state:'int', confirm:'bool'=False):
        if utils.isfile(self.repo_dir, host=self.prod_host):
            if not confirm:
                if not utils.confirm(f"Are you sure you want to change current production state for '{self.prod_domain}'?"):
                    log("Aborted", console=True)
                    return

        self.prod_state = new_state
        self.config("prod", True)
