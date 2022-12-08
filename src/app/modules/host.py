class Host:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]
        self.alias = hal.lmobjs[dbid][2]

        query = "select mac, storage, cpus, memory, net, ip, client, env, ssh_port, pg_port from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.storage, self.cpus, self.memory, self.net_dbid, self.ip, self.client_id, self.env, self.ssh_port, self.pg_port = hal.db.execute(query, params)[0]

        self.mnt_dir = utils.mnt_dir + self.alias if self.alias else self.lmid + "/"
        #self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.port, b.port from projects.webs a, projects.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def manage_service(self, action, service):
        log(f"Restarting {service} for {self.lmid} ...", console=True)
        cmd(f"sudo systemctl {action} {service} ")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for {self.lmid} ...")
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

        log(f"Configuring PostgreSQL for {self.lmid} ...", console=True)
        port = random.randint(4096, 8192)

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
        #utils.write(config_file, config, lines=True, owner="postgres")
        #cmd(f"sudo cp {hal.tpls_dir}db/pg_hba.tpl {pg_dir}pg_hba.conf")
        #cmd(f"sudo chown postgres:postgres {pg_dir}pg_hba.conf")
        self.manage_service("restart", "postgresql")

        # Update ports in project files and in db
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))
        project_ids = hal.db.execute("select project from project.dbs where host=%s", (self.dbid,))
        print(project_ids)

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
        log(f"Configuring Git for {self.lmid} ...", console=True)
        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.lmid,
            "email": f"{self.lmid}@{self.opts['gitlab']}",
            "gpg_key": gpg.get_privkey_id(self.lmid)
            })
        utils.write(f"/home/hal/.gitconfig", config)

    # Mount
    def is_mounted(self):
        # Warning! self.mnt_dir may not exist!
        # To do: Handle exception
        if len(os.listdir(self.mnt_dir)):
            return True
        return False

    def mount(self):
        if self.lmid == hal.host_lmid:
            log("You can't mount the host!", level=4, console=True)
        else:
            if not os.path.isdir(self.mnt_dir):
                log(f"Creating mount point at {self.mnt_dir} ...")
                cmd("mkdir " + self.mnt_dir)

            if not self.is_mounted():
                cmd(f"sshfs -p {self.ssh_port} -o identityfile={hal.gutil.ssh_dir}{self.lmid} hal@{self.ip}:/home {self.mnt_dir}")
                log(f"{self.lmid} mounted {util.now()}", console=True)
            else:
                log(f"{self.lmid} is already mounted!", console=True)

    def unmount(self):
        if self.lmid == hal.host_lmid:
            log("You can't unmount the host!", level=4, console=True)
        else:
            if self.is_mounted():
                cmd(f"fusermount -u {self.mnt_dir}")
                log(f"{self.lmid} unmounted {util.now()}", console=True)
            else:
                log(self.lmid + " is already unmounted!", console=True)

            # Double check that it's unmounted
            if not self.is_mounted() and os.path.isdir(self.mnt_dir):
                log(f"Removing mount point from {self.mnt_dir} ...")
                cmd("rm " + self.mnt_dir)

    def check(self):
        if self.dbid == hal.host_dbid and not self.pg_port:
            query = "update guests set pg_port=%s where lmobj=%s;"
            params = util.read(hal.app_dir + "db/details.ast").get("port"), self.dbid,
            hal.db.execute(query, params)
