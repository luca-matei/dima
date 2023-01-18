class HostServices:
    def manage_service(self, action, service):
        log(f"Restarting {service} for {self.name} ...", console=True)
        cmd(f"sudo systemctl {action} {service} ", host=self.lmid)

    def status_service(self, service):
        out = cmd(f"sudo systemctl status {service}", catch=True)
        if "active (running)" in out:
            log(f"{service} is active.", console=True)
            return 1

        elif "failed" in out:
            log(f"{service} failed!", level=4, console=True)
            return 0

    # Nets
    def config_dhcp(self):
        log(f"Configuring DHCP server on {self.name} ...", console=True)
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
        self.status_service("isc-dhcp-server")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for {self.name} ...")
        utils.copy(hal.tpls_dir + "web/nginx.tpl", "/etc/nginx/nginx.conf", host=self.lmid)
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
        self.status_service("nginx")

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
            if not utils.isfile(cfg_file + ".bak", host=self.lmid):
                utils.copy(cfg_file, cfg_file + ".bak", owner="postgres", host=self.lmid)

        # Modify port in config file
        config = utils.format_tpl("pg/postgresql.tpl", {
            "port": port
            })

        # Write new config file and restart service
        utils.write(config_file, config, owner="postgres", host=self.lmid)
        utils.copy(hal.tpls_dir + "pg/pg_hba.tpl", pg_dir + "pg_hba.conf", owner="postgres", host=self.lmid)

        # Update ports in Hal projects and in db
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))

        if self.dbid == hal.host_dbid:
            details_path = hal.app_dir + "db/details.ast"
            details = utils.read(details_path, host=self.lmid)
            details["port"] = port
            utils.write(details_path, details, host=self.lmid)

        self.pg_port = port
        self.manage_service("restart", "postgresql")

    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    def start_postgres(self):
        self.manage_service("start", "postgresql")

    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    def status_postgres(self):
        self.status_service("postgres")

    # Supervisor
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    def status_supervisor(self):
        self.status_service("supervisor")

    # SSH
    def config_ssh_client(self):
        if not utils.isfile("/home/hal/.ssh/", host=self.lmid):
            cmd("mkdir /home/hal/.ssh/", host=self.lmid)

        log(f"Configuring SSH client for {self.name} ...", console=True)
        hosts = ""

        if self.dbid == hal.host_dbid:
            query = "select a.lmid, a.alias, b.ip, b.ssh_port from lmobjs a, host.hosts b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,

            for host in hal.db.execute(query, params):
                hosts += utils.format_tpl("ssh/host.tpl", {
                    "lmid": host[0],
                    "ip": host[2],
                    "port": host[3],
                    "user": "hal",
                    "privkey": utils.ssh_dir + host[0],
                    })

                if host[1]:
                    hosts += utils.format_tpl("ssh/host.tpl", {
                        "lmid": host[1],
                        "ip": host[2],
                        "port": host[3],
                        "user": "hal",
                        "privkey": utils.ssh_dir + host[0],
                    })

        hosts += utils.format_tpl("ssh/host.tpl", {
            "lmid": self.gitlab.domain,
            "ip": self.gitlab.domain,
            "port": 22,
            "user": "git",
            "privkey": utils.ssh_dir + self.lmid + "-gitlab",
            })

        utils.write("/home/hal/.ssh/config", utils.format_tpl("ssh/client_config.tpl", {
            "hosts": hosts,
        }), host=self.lmid)

    def config_ssh_server(self):
        log(f"Configuring SSH server for {self.name} ...", console=True)
        port = self.next_port()

        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))

        if self.dbid != hal.host_dbid:
            config = utils.format_tpl("ssh/server_config.tpl", {
                "port": port,
                })

            utils.write("/etc/ssh/sshd_config", config, host=self.lmid)

        self.config_ssh_client()

    def create_ssh_key(self, gitlab=False):
        log(f"Generating SSH key to access {'Gitlab from ' if gitlab else ''}host '{self.name}'. This may take a while ...", console=True)

        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if gitlab else '')
        cmd(f'ssh-keygen -b 4096 -t ed25519 -a 100 -f {privkey} -q -N ""', host=self.lmid)

        if utils.isfile(privkey):
            cmd("chmod 600 " + privkey, host=self.lmid)
            cmd("chmod 600 " + privkey + ".pub", host=self.lmid)
            self.config_ssh_client()

            return 1
        else:
            log(f"Couldn't generate SSH key to access {'Gitlab from ' if gitlab else ''}host '{self.name}'!", level=4, console=True)

            return 0

    def delete_ssh_key(self, gitlab=False):
        log(f"Removing {'Gitlab ' if gitlab else ''}SSH key for host '{self.name}' ...", console=True)

        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if gitlab else '')
        cmd(f"rm {privkey} {privkey}.pub", host=self.lmid)

        self.config_ssh_client()


class Host(lmObj, HostServices):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select mac, net, ip, client, env, ssh_port, pg_port from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.net_id, self.ip, self.client_id, self.env, self.ssh_port, self.pg_port = hal.db.execute(query, params)[0]

        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.gitlab = Gitlab(self.dbid, self.lmid)

        self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.port, b.port from web.webs a, project.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def has_storage(self, capacity):
        return True

    # Projects
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
        if utils.isfile(utils.ssl_dir + "dhparam.pem", host=self.lmid):
            log("DH parameters are already in place!")
            yes = utils.yes_no("Purge them?")

            if yes: cmd(f"rm {utils.ssl_dir}dhparam.pem", host=self.lmid)
            else: return

        log("Generating DH params. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096", host=self.lmid)

    # Hosts
    def create_host(self, env="dev", alias=None, mem=1024, cpus=1, disk=2):
        log("Creating new VM ...", console=True)
        lmid = hal.next_lmid()
        hostname = alias if alias else lmid

        query = "select lmobj from nets where pm=%s;"
        params = self.dbid,
        vm_net_id = hal.db.execute(query, params)[0][0]

        ip = utils.get_free_ip(vm_net_id)
        utils.hosts.preseed_host(hostname, vm_net_id, ip)

        cmd(f"sudo virt-install " + ' '.join([
            f"--name {hostname}",
            f"--memory {mem}",
            f"--vcpus {cpus}",
            f"--cdrom {utils.tmp_dir + hostname}.iso",
            "--os-variant generic",
            f"--disk {utils.vms_dir + lmid}.qcow2,size={disk},format=qcow2,cache=none",
            f"--network network={hal.pools.get(vm_net_id).lmid}",
            "--noautoconsole",
            ]), host=self.lmid)

        if utils.isfile(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid):
            mac = re.compile("<mac address='(.*?)'/>").search(utils.read(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid)).group(1)

            dbid = hal.insert_lmobj(lmid, 'Host', alias)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = dbid, mac, vm_net_id, ip, None, utils.envs.get(env), None, None, self.dbid,

            hal.db.execute(query, params)
            self.config_dhcp()

            log(f"{hostname} VM created on {self.name}!", console=True)

        log(f"Couldn't create {hostname} VM on {self.name}!", level=4, console=True)

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

    # System
    def update(self):
        log(f"Updating {self.lmid} ...", console=True)
        cmd("apt update && apt upgrade -y", host=self.lmid)

    def reboot(self):
        log(f"Rebooting {self.lmid} ...", console=True)
        cmd("sudo systemctl reboot now", host=self.lmid)

    def check(self):
        if not self.ssh_port:
            self.config_ssh_server()

        if not self.pg_port:
            self.config_postgres()

        print(cmd("echo 1", catch=True, host=self.lmid))
