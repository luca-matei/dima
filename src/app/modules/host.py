class Guest:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]

        query = "select mac, storage, cpus, memory, net, ip, client, env, ssh_port, pg_port, pm from hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.storage, self.cpus, self.memory, self.net_dbid, self.ip, self.client_id, self.env, self.ssh_port, self.pg_port, self.pm_id = hal.db.execute(query, params)[0]

        self.mnt_dir = utils.mnt_dir + self.lmid + "/"
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

    def config(self, service=""):
        if service in ("postgresql", "nginx"):
            getattr(self, "config_" + service)()

    def config_nginx(self):
        log(f"Configuring Nginx for {self.lmid} ...")
        cmd(f"sudo cp {hal.tpl_dir}web/nginx.tpl /etc/nginx/nginx.conf")
        self.restart("nginx")

    def restart(self, service=""):
        services = ("postgresql", "nginx", "supervisor")
        if service in services:
            log(f"Restarting {service} for {self.lmid} ...", console=True)
            cmd(f"sudo systemctl restart " + service)
        else:
            log(f"Can't restart service '{service}'!")

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
