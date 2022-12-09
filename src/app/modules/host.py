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
