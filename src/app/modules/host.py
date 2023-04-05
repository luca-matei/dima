class HostServices:
    pg_version = 13

    def manage_service(self, action, service):
        messages = {
            "start": "Starting",
            "stop": "Stopping",
            "restart": "Restarting",
            "reload": "Reloading",
            "enable": "Enabling",
            "disable": "Disabling",
            }

        if service == "postgresql":
            if action == "status":
                pass
            else:
                cmd(f"sudo pg_ctlcluster {self.pg_version} main {action}", host=self.lmid)
        else:
            if action == "status":
                out = cmd(f"sudo systemctl status {service}", catch=True)
                if "active (running)" in out:
                    log(f"{service} is active", console=True)
                    return 1

                elif "failed" in out:
                    log(f"{service} failed!", level=4, console=True)
                    return 0
            else:
                msg = messages.get(action)
                log(f"{msg} {service} for '{self.name}' ...", console=True)
                cmd(f"sudo systemctl {action} {service} ", host=self.lmid)
                log(f"{msg[:-3]}ed {service} for '{self.name}'", console=True)

    # Nets
    def config_dhcp(self):
        log(f"Configuring DHCP server on '{self.name}' ...", console=True)
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
        self.manage_service("status", "isc-dhcp-server")

    def get_iface(self):
        return "ens3"

    # Firewall
    def config_firewall(self):
        log(f"Configuring Firewall for '{self.name}' ...", console=True)
        self.manage_service("enable", "nftables")

        if not utils.isfile("/etc/nft/", host=self.lmid):
            cmd("sudo mkdir /etc/nft/", host=self.lmid)

        nftables = utils.format_tpl("nftables/nftables.tpl", {
            "iface": self.get_iface(),
            "ssh_port": self.ssh_port,
            })

        utils.write("/etc/nftables.conf", nftables, host=self.lmid)
        self.send_file(hal.tpls_dir + "nftables/bogons-ipv4.tpl", "/etc/nft/bogons-ipv4.nft")
        self.send_file(hal.tpls_dir + "nftables/black-ipv4.tpl", "/etc/nft/black-ipv4.nft")
        self.manage_service("restart", "nftables")
        log(f"Configured Firewall for '{self.name}'", console=True)

    def enable_firewall(self):
        self.manage_service("enable", "nftables")

    def disable_firewall(self):
        self.manage_service("disable", "nftables")

    def start_firewall(self):
        self.manage_service("start", "nftables")

    def stop_firewall(self):
        self.manage_service("stop", "nftables")

    def restart_firewall(self):
        self.manage_service("restart", "nftables")

    # Nginx
    def config_nginx(self):
        log(f"Configuring Nginx for '{self.name}' ...")
        self.send_file(hal.tpls_dir + "web/nginx.tpl", "/etc/nginx/nginx.conf")
        cmd("sudo rm /etc/nginx/sites-enabled/default", host=self.name)
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
        self.manage_service("status", "nginx")

    # Postgres
    def create_pg_role(self, role:'str', password:'str'=None):
        # https://www.postgresql.org/docs/current/sql-createrole.html
        log(f"Creating '{role}' Postgres role on '{self.name}' ...", console=True)
        if not password:
            password = utils.new_pass(64)

        role_query = utils.dbs.query.format(f"create role {role} with login password '{password}';")
        output = cmd(role_query, catch=True, host=self.lmid)
        if "already exists" in output:
            if utils.confirm(f"'{role}' role already exists on '{self.name}'! Purge it?"):
                cmd(utils.dbs.query.format(f"drop database if exists {role}; drop role if exists {role};"), host=self.lmid)
            else: return

            cmd(role_query, host=self.lmid)

        cmd(utils.dbs.query.format(f"grant {role} to hal;"), host=self.lmid)

        if role.startswith("lm"):
            utils.write(utils.projects_dir + role + "/src/app/db/db_pass", password, host=self.lmid)
            return password

        else:
            utils.write(utils.tmp_dir + "db_pass.tmp", password)
            log(f"Password stored in {utils.tmp_dir}db_pass.tmp!", console=True)

        log(f"Postgres role '{role}' created on '{self.name}'", console=True)

    def create_pg_db(self, db:'str'):
        log(f"Creating '{db}' Postgres database on '{self.name}' ...", console=True)
        db_query = utils.dbs.query.format(f"create database {db} owner {db} encoding 'utf-8';")
        output = cmd(db_query, catch=True, host=self.lmid)
        if "already exists" in output:
            if utils.confirm(f"'{db}' database already exists on '{self.name}'! Purge it?"):
                cmd(utils.dbs.query.format(f"drop database {db};"), host=self.lmid)
            else: return

            cmd(db_query, catch=True, host=self.lmid)

        log(f"Postgres database '{db}' created on '{self.name}'", console=True)

    def config_postgres(self):
        """
        Manages /etc/postgresql/13/main/postgresql.conf
                /etc/postgresql/13/main/pg_hba.conf
        Assigns a new port to the PostgreSQL server.
        """

        log(f"Configuring PostgreSQL for '{self.name}' ...", console=True)
        port = self.next_port(service=True)

        pg_dir = f"/etc/postgresql/{self.pg_version}/main/"
        config_file = pg_dir + "postgresql.conf"
        hba_file = pg_dir + "pg_hba.conf"

        # Create backup for default configs
        for cfg_file in (config_file, hba_file):
            if not utils.isfile(cfg_file + ".bak", host=self.lmid):
                utils.copy(cfg_file, cfg_file + ".bak", owner="postgres", host=self.lmid)

        # Modify port in config file
        config = utils.format_tpl("pg/postgresql.tpl", {
            "listen": "" if self.dbid == hal.host_dbid else "," + self.ip,
            "port": port
            })

        # Allow remote access
        hba = utils.format_tpl("pg/pg_hba.tpl", {
            "remote_auth": "" if self.dbid == hal.host_dbid else f"host all all {hal.pools.get(hal.host_dbid).ip}/32 scram-sha-256"
            })

        # Write new config file and restart service
        utils.write(config_file, config, owner="postgres", tpl=True, host=self.lmid)
        utils.write(hba_file, hba, owner="postgres", tpl=True, host=self.lmid)

        # Update ports in Hal projects and in db
        utils.write(utils.dbs.port_file, str(port), host=self.lmid)
        hal.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))
        log(f"Assigned Postgres port {port} to '{self.name}'", console=True)

        self.pg_port = port
        self.manage_service("restart", "postgresql")

        query = utils.dbs.query.replace("hal", "postgres")
        has_db = cmd(query.format(f"select 1 from pg_database where datname='hal';"), catch=True, host=self.lmid)

        if not has_db:
            cmd(query.format(f"create role hal with login createdb createrole password '{utils.new_pass(64)}';"), host=self.lmid)
            cmd(query.format("create database hal owner hal encoding 'utf-8';"), host=self.lmid)

        log(f"Configured PostgreSQL for '{self.name}'", console=True)

    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    def start_postgres(self):
        self.manage_service("start", "postgresql")

    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    def status_postgres(self):
        self.manage_service("status", "postgresql")

    # Supervisor
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    def status_supervisor(self):
        self.manage_service("status", "supervisor")

    # SSH
    def restart_ssh(self):
        self.manage_service("restart", "ssh")

    def config_ssh_client(self):
        if not utils.isfile("/home/hal/.ssh/", host=self.lmid):
            cmd("mkdir /home/hal/.ssh/", host=self.lmid)

        log(f"Configuring SSH Client for '{self.name}' ...", console=True)
        hosts = []

        if self.dbid == hal.host_dbid:
            query = "select a.lmid, a.alias, b.ip, b.ssh_port from lmobjs a, host.hosts b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,

            for host in hal.db.execute(query, params):
                hosts.append(utils.format_tpl("ssh/host.tpl", {
                    "lmid": host[0],
                    "ip": host[2],
                    "port": host[3],
                    "user": "hal",
                    "privkey": utils.ssh_dir + host[0],
                    }))

                if host[1]:
                    hosts.append(utils.format_tpl("ssh/host.tpl", {
                        "lmid": host[1],
                        "ip": host[2],
                        "port": host[3],
                        "user": "hal",
                        "privkey": utils.ssh_dir + host[0],
                    }))

        hosts.append(utils.format_tpl("ssh/host.tpl", {
            "lmid": gitlab.domain,
            "ip": gitlab.domain,
            "port": 22,
            "user": "git",
            "privkey": utils.ssh_dir + self.lmid + "-gitlab",
            }))

        hosts = '\n\n'.join(hosts)

        utils.write("/home/hal/.ssh/config", hosts, tpl=True, host=self.lmid)
        self.update_hosts_file()

        log(f"Configured SSH Client for '{self.name}'", console=True)

    def config_ssh_server(self):
        if self.ssh_port == -1:
            log(f"'{self.name}' is not a SSH Server!", level=4, console=True)
        else:
            log(f"Configuring SSH Server for '{self.name}' ...", console=True)
            port = self.next_port(service=True)
            self.port = port

            hal.db.execute("update host.hosts set ssh_port=%s where lmobj=%s;", (port, self.dbid))

            config = utils.format_tpl("ssh/server_config.tpl", {
                "port": port,
                })

            utils.write("/etc/ssh/sshd_config", config, tpl=True, host=self.lmid)
            self.config_firewall()
            self.restart_ssh()
            hal.pools.get(hal.host_dbid).config_ssh_client()

            log(f"Configured SSH Server for '{self.name}'", console=True)

    def create_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Generating SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'. This may take a while ...", console=True)

        host = self.lmid if for_gitlab else hal.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        if utils.isfile(privkey, host=host):
            if utils.confirm("SSH key already exists! Overwrite it?"):
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(ssh.keygen.format(privkey), host=host)

        log(f"SSH Key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}' generated", console=True)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)

            if for_gitlab:
                self.config_ssh_client()
                gitlab.add_ssh_key(self.lmid, utils.read(utils.ssh_dir + self.lmid + "-gitlab.pub", host=self.lmid))
            else:
                hal.pools.get(hal.host_dbid).config_ssh_client()

            return 1
        else:
            log(f"Couldn't generate SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'!", level=4, console=True)

            return 0

    def delete_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Removing {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}' ...", console=True)

        host = self.lmid if for_gitlab else hal.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        cmd(f"rm {privkey} {privkey}.pub", host=host)

        log(f"Removed {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}'", console=True)

    ## GPG
    def get_gpg_pubkey(self, email:'str'=None):
        log(f"Getting GPG pubkey for {email} ...", console=True)
        if not email: email = self.email
        pubkey_path = utils.tmp_dir + "gpg_pubkey"
        output = cmd(f"gpg2 --export -a {self.get_gpg_key_id(email)} > {pubkey_path}", catch=True, host=self.lmid)

        if "nothing exported" in output:
            log(f"Couldn't get GPG pubkey for {email}!", level=4, console=True)

        else:
            log(f"GPG pubkey for {email} saved at {pubkey_path}!", console=True)
            return utils.read(pubkey_path, host=self.lmid)

    def get_gpg_key_id(self, email:'str'=None):
        if not email: email = self.email
        key_id = cmd(f"gpg2 --list-keys --keyid-format LONG {email}", catch=True, host=self.lmid)

        if "No public key" in key_id:
            if utils.confirm(f"Couldn't find GPG key for '{email}'! Create one?"):
                return self.create_gpg_key(email)
            return 0
        else:
            return re.findall(r'\bpub   rsa4096/\w+', key_id)[0].split('/')[1]

    def create_gpg_key(self, email:'str'=None):
        if not email: email = self.email
        log(f"Generating GPG Key for '{email}'. This may take a while ...", console=True)

        key_config = utils.format_tpl("gpg-key.tpl", {
            "user": email.split('@')[0],
            "email": email
            })
        utils.write(utils.tmp_dir + "gpg_batch", key_config, host=self.lmid)

        log(f"Generated GPG Key for '{email}'", console=True)

        cmd(f"gpg2 --batch --gen-key {utils.tmp_dir}gpg_batch", host=self.lmid)
        key_id = self.get_gpg_key_id(email)
        log(f"Key ID: {key_id}", console=True)

        return key_id

    def delete_gpg_key(self, email:'str'=None):
        log(f"Removing GPG Key for '{email}' ...", level=3, console=True)
        if not email: email = self.email
        cmd(f"gpg2 --batch --delete-secret-keys {email}", host=self.lmid)
        cmd(f"gpg2 --batch --delete-keys {email}", host=self.lmid)
        log(f"Removed GPG key for '{email}'!", level=3, console=True)


class Host(lmObj, HostServices):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select mac, net, ip, client, env, ssh_port, pg_port, pm from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.net_id, self.ip, self.client_id, self.env_id, self.ssh_port, self.pg_port, self.pm_id = hal.db.execute(query, params)[0]

        self.env = utils.hosts.envs.get(self.env_id)
        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.email = self.lmid + "@" + utils.hosts.domain
        self.check()

    def next_port(self, service=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port]

        else:
            min, max = 16384, 32768
            used = []
            for ports in hal.db.execute("select a.dev_port, a.prod_port, b.port from web.webs a, project.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    def has_storage(self, capacity):
        return True

    # Projects
    def create_project(self, lmid, module, alias, name, description):
        if gitlab.create_project(data={
            'path': lmid,
            'name': name,
            'description': description,
            'visibility': 'private',
            'initialize_with_readme': True,
            }):

            dbid = hal.insert_lmobj(lmid, module, alias)

            query = f"insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = dbid, self.dbid, 0.1, self.dbid, 0.1, name, description,
            hal.db.execute(query, params)

            self.clone_repo(lmid)
            return dbid

        return 0

    def clone_repo(self, path:'str'):
        log(f"Cloning '{path}' Gitlab repository ...", console=True)
        cmd(f"git clone git@{gitlab.domain}:{gitlab.user}/{path}.git {utils.projects_dir}{path}/", host=self.lmid)
        log(f"'{path}' cloned", console=True)

    # Web
    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=("static",), langs:'list'=("en",), themes:'list'=("light",), default_lang:'str'="en", default_theme:'str'="light", has_animations:'bool'=False):

        # To do: validate parameters

        #if hal.domains.get(domain):
            #log("Domain already exists!", level=4, console=True)
            #return 0

        lmid = hal.next_lmid()
        dbid = self.create_project(lmid, "Web", alias, name, description)

        if dbid:
            module_ids = [x for x in [utils.webs.modules.get(m, 0) for m in modules] if x]
            lang_ids = [x for x in [utils.projects.langs.get(l, 0) for l in langs] if x]
            theme_ids = [x for x in [utils.projects.themes.get(t, 0) for t in themes] if x]

            query = "insert into web.webs (lmobj, domain, dev_port, prod_port, dev_ssl_due, prod_ssl_due, prod_state, modules, langs, themes, default_lang, default_theme, has_animations) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id;"
            params = hal.lmobjs[lmid], domain, self.next_port(), self.next_port(), None, None, 0, module_ids, lang_ids, theme_ids, utils.projects.langs[default_lang], utils.projects.themes[default_theme], has_animations,

            if hal.db.execute(query, params)[0][0]:
                log(f"{name if name else (alias if alias else lmid)} web app created!", console=True)
                hal.create_pool(dbid)
                self.update_hosts_file()
                return 1

        log(f"Couldn't create web app '{lmid}'!", level=4, console=True)

    def generate_dh(self):
        if utils.isfile(utils.ssl_dir + "dhparam.pem", host=self.lmid):
            if utils.confirm("DH parameters are already in place! Purge them?"):
                cmd(f"rm {utils.ssl_dir}dhparam.pem", host=self.lmid)
            else:
                return

        log(f"Generating DH params for '{self.name}'. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096", host=self.lmid)
        log(f"Generated DH params for '{self.name}'", console=True)

    # Hosts
    def create_host(self, env:'str'="dev", alias:'str'=None, mem:'int'=1024, cpus:'int'=1, disk:'int'=5):
        log("Creating new VM ...", console=True)
        lmid = hal.next_lmid()

        ip = utils.nets.get_free_ip(self.net_id)
        ssh.create_ssh_key(lmid)
        ssh_port = self.next_port(service=True)
        utils.hosts.preseed_host(lmid, self.net_id, ip, ssh_port, host=self.lmid)

        output = cmd(f"sudo virt-install " + ' '.join([
            f"--name {lmid}",
            f"--memory {mem}",
            f"--vcpus {cpus}",
            f"--cdrom {utils.tmp_dir + lmid}.iso",
            "--os-variant generic",
            f"--disk {utils.vms_dir + lmid}.qcow2,size={disk},format=qcow2,cache=none",
            f"--network bridge={self.lmid}",
            "--noautoconsole",
            ]), host=self.lmid)

        if utils.isfile(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid):
            mac = re.compile("<mac address='(.*?)'/>").search(utils.read(f"/etc/libvirt/qemu/{lmid}.xml", host=self.lmid)).group(1)

            dbid = hal.insert_lmobj(lmid, 'Host', alias)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = dbid, mac, self.net_id, ip, None, utils.hosts.envs.get(env), ssh_port, self.next_port(service=True), self.dbid,

            hal.db.execute(query, params)
            hal.pools.get(hal.host_dbid).config_ssh_client()

            log(f"'{lmid}' VM created on '{self.name}'", console=True)
            hal.create_pool(dbid)

        else:
            log(f"Couldn't create '{lmid}' VM on '{self.name}'!", level=4, console=True)

    # Mount
    def is_mounted(self):
        if len(os.listdir(self.mnt_dir)):
            return True
        return False

    def mount(self):
        if self.dbid == hal.host_dbid:
            log("You can't mount the host!", level=4, console=True)
        else:
            if not utils.isfile(self.mnt_dir):
                log(f"Creating mount point at '{self.mnt_dir}' ...")
                cmd("mkdir " + self.mnt_dir)

            if not self.is_mounted():
                cmd(f"sshfs -p {self.ssh_port} -o allow_other,identityfile={utils.ssh_dir}{self.lmid} hal@{self.ip}:/home/hal {self.mnt_dir}")
                log(f"'{self.name}' mounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already mounted!", level=4, console=True)

    def unmount(self):
        if self.dbid == hal.host_dbid:
            log("You can't unmount the host!", level=4, console=True)
        else:
            if self.is_mounted():
                cmd(f"fusermount -u {self.mnt_dir}")
                log(f"'{self.name}' unmounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already unmounted!", level=4, console=True)

    # System
    def config_sysctl(self):
        log(f"Configuring sysctl for '{self.name}' ...", console=True)
        sysctl = utils.format_tpl("sysctl.tpl", {
            "iface": self.get_iface()
            })
        utils.write("/etc/sysctl.conf", sysctl, tpl=True, host=self.lmid)
        cmd("sudo sysctl -p", host=self.lmid)
        log(f"Configured sysctl for '{self.name}'", console=True)

    def config_grub(self):
        log(f"Configuring GRUB for '{self.name}' ...", console=True)
        self.send_file(hal.tpls_dir + "grub.tpl", "/etc/default/grub")
        cmd("sudo update-grub", host=self.lmid)
        log(f"Configured GRUB for '{self.name}'", console=True)

    def config_motd(self):
        self.send_file(hal.tpls_dir + "motd.tpl", "/etc/motd")

    def update_resources(self):
        log(f"Updating resources for '{self.name}' ...", console=True)
        if self.dbid != hal.host_dbid:
            cmd(f"rm -r {utils.res_dir}web/", host=self.lmid)
            self.send_file(utils.res_dir + "web/", utils.res_dir + "web/")
        else:
            # Download resources
            pass
        log(f"Updated resources for '{self.name}'", console=True)

    def update_hosts_file(self):
        def append_web(web):
            # Prod host
            if web[0] == self.ip:
                web[0] = "127.0.0.1"

            fill_spaces1 = (len("255.255.255.255") - len(web[0]))*' ' + spaces
            fill_spaces2 = (len("test.testing.lucamatei.shop") - len(web[2]))*' ' + spaces

            hosts.append(web[0] + fill_spaces1 + web[2] + fill_spaces2 + web[3])

            # Dev host
            if web[1] == self.ip:
                web[1] = "127.0.0.1"

            fill_spaces1 = (len("255.255.255.255") - len(web[1]))*' ' + spaces
            web[2] = "dev." + web[2]
            fill_spaces2 = (len("test.testing.lucamatei.shop") - len(web[2]))*' ' + spaces

            hosts.append(web[1] + fill_spaces1 + web[2] + fill_spaces2 + "dev." + web[3])


        log(f"Generating /etc/hosts for '{self.name}' ...", console=True)
        spaces = 4 * ' '
        hosts = [
            f"127.0.1.1{spaces}{self.lmid}.{utils.hosts.domain}{spaces*2}{self.lmid}"
            ]

        if self.name != self.lmid:
            hosts.append(f"127.0.1.1{spaces}{self.name}.{utils.hosts.domain}{spaces}{self.name}")

        host_entry = '\n'.join(hosts)
        hosts = []

        if self.dbid == hal.host_dbid:
            # Hosts
            query = "select a.ip, b.lmid, b.alias from host.hosts a, lmobjs b where b.id = a.lmobj and b.id != %s;"
            params = self.dbid,
            db_hosts = [list(h) for h in hal.db.execute(query, params)]

            for host in db_hosts:
                fill_spaces1 = (len("255.255.255.255") - len(host[0]))*' ' + spaces
                fill_spaces2 = (len("astatin") - len(host[1]))*' ' + spaces

                hosts.append(host[0] + fill_spaces1 + host[1] + '.' + utils.hosts.domain + fill_spaces2 + host[1])

                # Has alias
                if host[2]:
                    fill_spaces3 = (len("astatin") - len(host[2]))*' ' + spaces
                    hosts.append(host[0] + fill_spaces1 + host[2] + '.' + utils.hosts.domain + fill_spaces3 + host[2])

            host_entries = "\n".join(hosts)
            hosts = []

            # Web apps
            query = "select a.ip, b.ip, c.name, d.lmid from host.hosts a, host.hosts b, domains c, lmobjs d, web.webs e, project.projects f where a.lmobj = f.prod_host and b.lmobj = f.dev_host and c.id = e.domain and d.id = e.lmobj and d.id = f.lmobj;"
            db_webs = [list(h) for h in hal.db.execute(query, params)]

            for web in db_webs:
                append_web(web)
        else:
            host_entries = ""
            query = "select a.ip, b.ip, c.name, d.lmid from host.hosts a, host.hosts b, domains c, lmobjs d, web.webs e, project.projects f where a.lmobj = f.prod_host and b.lmobj = f.dev_host and c.id = e.domain and d.id = e.lmobj and d.id = f.lmobj and c.name=%s;"
            #params = utils.webs.assets_domain,
            #web = list(hal.db.execute(query, params)[0])

            #append_web(web)

        web_entries = "\n".join(hosts)

        hosts_file = utils.format_tpl("hosts.tpl", {
            "host": host_entry,
            "hosts": host_entries,
            "webs": web_entries
            })
        utils.write("/etc/hosts", hosts_file, host=self.lmid)

        log(f"Generated /etc/hosts for '{self.name}'", console=True)

    def ping(self):
        log(f"Trying to ping '{self.name}' ...", console=True)
        if self.dbid == hal.host_dbid:
            print("It's this machine, dumbass!")
        else:
            response = cmd("echo 1", catch=True, host=self.lmid)
            if response == "1":
                log(f"Host '{self.name}' reached!", console=True)
            else:
                log(f"Couldn't reach host '{self.name}'!", level=3, console=True)

    def build_dir_tree(self):
        log(f"Creating Hal's directory tree on '{self.name}' ...", console=True)

        dir_tree = [
            utils.logs_dir,
            utils.projects_dir,
                utils.projects_dir + "pids/",
            utils.res_dir,
                utils.res_dir + "web/",
                utils.res_dir + "web/css/",
                utils.res_dir + "web/js/",
                utils.res_dir + "web/fonts/",
                utils.res_dir + "web/icons/",
            utils.ssl_dir,
            utils.tmp_dir
            ]

        if not self.pm_id:
            dir_tree.extend([utils.vms_dir])

        if self.env == "dev":
            dir_tree.extend([utils.ssh_dir])

        utils.create_dir_tree(dir_tree)
        cmd(f"sudo chown www-data:www-data {utils.projects_dir}pids", host=self.lmid)

    def build_venv(self):
        if utils.isfile(f"{utils.projects_dir}venv/", host=self.lmid):
            if utils.confirm(f"There's already a virtual environment on '{self.name}'! Purge it?"):
                cmd(f"rm -r {utils.projects_dir}venv/", host=self.lmid)
            else:
                return

        log(f"Creating virtual environment for '{self.name}' ...", console=True)
        cmd(f"python3 -m venv {utils.projects_dir}venv", host=self.lmid)

        packages = "netifaces requests uwsgi libsass ruamel.yaml psycopg2 markdown markdown-katex"

        cmd(f"{utils.projects_dir}venv/bin/pip install wheel", host=self.lmid)
        cmd(f"{utils.projects_dir}venv/bin/pip install {packages}", host=self.lmid)

        log(f"Created virtual environment for '{self.name}'", console=True)

    def config_git(self):
        log(f"Configuring Git for '{self.name}' ...", console=True)

        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.lmid,
            "email": self.email,
            "gpg_key_id": self.get_gpg_key_id(self.email),
            })

        utils.write(f"/home/hal/.gitconfig", config, tpl=True, host=self.lmid)

        exists = False
        gpg_pubkey = self.get_gpg_pubkey(self.email)
        gpg_keys = gitlab.request(endpoint = f"/user/gpg_keys")

        for k in gpg_keys:
            if k["key"] == gpg_pubkey:
                exists = True
                break

        if not exists:
            gitlab.add_gpg_key(self.email, gpg_pubkey)

        log(f"Configured Git for '{self.name}'", console=True)

    def setup(self):
        self.config_ssh_server()
        self.config_grub()
        self.config_motd()
        self.config_sysctl()

        self.build_dir_tree()
        self.build_venv()
        self.update_resources()

        self.generate_dh()
        self.config_nginx()
        self.config_postgres()

        if self.env == "dev":
            self.config_git()
            self.create_ssh_key(for_gitlab=True)

    def has_file(self, path:'str'):
        if utils.isfile(path, host=self.lmid):
            log("File exists!", console=True)

    def send_file(self, src_path:'str', dest_path:'str', owner:'str'="root"):
        is_dir = src_path.endswith('/')

        final_path = None
        if dest_path.startswith("/etc/"):
            final_path = dest_path
            dest_path = utils.tmp_dir + 'restricted' + ('/' if is_dir else '')

        cmd(f"scp {'-r ' if is_dir else ''}-P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} {src_path.rstrip('/')} hal@{self.lmid}:{dest_path.rstrip('/')}", catch=True)

        if final_path:
            cmd(f"sudo mv {dest_path} {final_path}", host=self.lmid)
            if owner != "root": cmd(f"sudo chown {owner}:{owner} {final_path}", host=self.lmid)

    def retrieve_file(self, src_path:'str', dest_path:'str'):
        # Handle permissions
        cmd(f"scp -P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} hal@{self.lmid}:{src_path} {dest_path}", catch=True)

    def status(self):
        print("OK")

    def update(self):
        log(f"Updating '{self.name}' ...", console=True)
        cmd("apt update && apt upgrade -y", host=self.lmid)
        log(f"Updated '{self.name}'", console=True)

    def reboot(self):
        log(f"Rebooting '{self.name}' ...", console=True)
        cmd("sudo systemctl reboot now", host=self.lmid)
        log(f"Rebooted '{self.name}'", console=True)

    def check(self):
        pass
