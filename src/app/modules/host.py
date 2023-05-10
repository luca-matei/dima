class HostServices:
    pg_version = 13

    @authorize
    def manage_service(self, action, service):
        messages = {
            "start": "Starting",
            "stop": "Stopping",
            "restart": "Restarting",
            "reload": "Reloading",
            "enable": "Enabling",
            "disable": "Disabling",
            }

        # To do: Check for service

        if service == "postgresql":
            if action == "status":
                pass
            else:
                cmd(f"sudo pg_ctlcluster {self.pg_version} main {action}", host=self.lmid)
        else:
            if action == "status":
                out = cmd(f"sudo systemctl status {service}", catch=True, host=self.lmid)
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

    # NET

    @authorize
    def get_iface(self):
        return [x for x in cmd("ls /sys/class/net", catch=True, host=self.lmid).split('\n') if x.startswith(("eth", "eno", "enp", "ens"))][0]
        return "eth0"

    # DHCP

    @authorize
    def config_dhcp(self):
        if "dhcp" not in self.services:
            log(f"Host '{self.name}' isn't a DHCP server!", level=4, console=True)
            return

        log(f"Configuring DHCP server on '{self.name}' ...", console=True)
        query = "select a.lmid, b.lmobj, b.dns, c.name, b.netmask, b.gateway, b.lease_start, b.lease_end from lmobjs a, nets b, domains c where a.id = b.lmobj and c.id=b.domain and b.dhcp=%s;"
        params = self.dbid,
        nets = dima.db.execute(query, params)
        print(nets)

        if not nets:
            log("There are no networks managed by this DHCP server!", level=4, console=True)
            return

        net_fields = "lmid", "dbid", "dns_dbid", "domain", "netmask", "gateway", "lease_start", "lease_end",
        host_fields = "lmid", "mac", "ip",

        for n in nets:
            net = dict(zip(net_fields, n))
            net_obj = ipaddress.ip_network(net.get("gateway") + "/" + net.get("netmask"), strict=False)
            subnet = str(net_obj).split('/')[0]
            broadcast = str(net_obj[-1])

            if net.get("dbid") == dima.net_dbid:
                # Main config
                dhcp_config = utils.format_tpl("dhcp/dhcpd.tpl", {
                    "domain": net.get("domain"),
                    "dns": f"{dima.pools.get(net.get('dns_dbid')).ip}, 8.8.8.8"
                    })

                # default file
                init_config = utils.format_tpl("dhcp/default.tpl", {
                    "interfaces": self.get_iface(),
                    })

                # Create subnets and hosts directory
                if not utils.isfile("/etc/dhcp/dhcp.d/", host=self.lmid):
                    cmd("sudo mkdir /etc/dhcp/dhcp.d/", host=self.lmid)

                # Write subnets file
                subnets_config = utils.format_tpl("dhcp/subnet.tpl", {
                    "subnet": subnet,
                    "netmask": net.get("netmask"),
                    "gateway": net.get("gateway"),
                    "broadcast": broadcast,
                    "lease_start": net.get("lease_start"),
                    "lease_end": net.get("lease_end")
                    })

                # Write hosts file
                query = "select a.lmid, b.mac, b.ip from lmobjs a, host.hosts b where a.id=b.lmobj and b.net=%s;"
                params = net.get("dbid"),
                hosts = dima.db.execute(query, params)

                hosts_config = ""
                for h in hosts:
                    host = dict(zip(host_fields, h))
                    host_config = utils.format_tpl("dhcp/host.tpl", {
                        "lmid": host.get("lmid"),
                        "mac": host.get("mac"),
                        "ip": host.get("ip")
                        })

                    hosts_config += host_config + '\n\n'

                utils.write('/etc/dhcp/dhcpd.conf', dhcp_config, host=self.lmid)
                utils.write("/etc/default/isc-dhcp-server", init_config, host=self.lmid)
                utils.write("/etc/dhcp/dhcp.d/subnets.conf", subnets_config, host=self.lmid)
                utils.write('/etc/dhcp/dhcp.d/hosts.conf', hosts_config, host=self.lmid)

                self.restart_dhcp()

            else:
                query = "select a.lmid, b.mac, b.ip from lmobjs a, host.hosts b where a.id=b.lmobj and a.net=%s;"
                params = net.get("dbid"),
                hosts = dima.db.execute(query, params)

                hosts_config = '\n'.join(['<host mac="{}" ip="{}"/>'.format(host.get('mac'), host.get('ip')) for host in hosts])

                net_xml = utils.format_tpl("dhcp/net.tpl", {
                    "lmid": net.get("lmid"),
                    "netmask": net.get("netmask"),
                    "gateway": net.get("gateway"),
                    "hosts": hosts_config
                    })

    @authorize
    def enable_dhcp(self):
        self.manage_service("enable", "isc-dhcp-server")

    @authorize
    def disable_dhcp(self):
        self.manage_service("disable", "isc-dhcp-server")

    @authorize
    def start_dhcp(self):
        self.manage_service("start", "isc-dhcp-server")

    @authorize
    def stop_dhcp(self):
        self.manage_service("stop", "isc-dhcp-server")

    @authorize
    def restart_dhcp(self):
        self.manage_service("restart", "isc-dhcp-server")

    @authorize
    def status_dhcp(self):
        self.manage_service("status", "isc-dhcp-server")

    # DNS

    @authorize
    def config_dns(self):
        # https://wiki.debian.org/Bind9#Introduction

        if "dns" not in self.services:
            log(f"Host '{self.name}' isn't a DNS server!", level=4, console=True)
            return

        log(f"Configuring DNS server on {self.lmid} ...", console=True)

        # /etc/default/bind9
        self.send_file(dima.tpls_dir + "dns/default.tpl", "/etc/default/named")

        # /etc/bind/named.conf.options
        utils.write("/etc/bind/named.conf.options", utils.format_tpl("dns/options.tpl", {
            "ip": self.ip,
            }), owner="root:bind", host=self.lmid)

        query = "select a.lmobj from host.hosts a, nets b where a.net=b.lmobj and b.dns=%s;"
        params = self.dbid,
        hosts = dima.db.execute(query, params)

        # Zones
        query = "select a.lmid, b.dev_host, b.prod_host, c.name from lmobjs a, project.projects b, domains c, web.webs d where a.id=b.lmobj and b.lmobj=d.lmobj and c.id=d.domain;"
        webs = dima.db.execute(query)

        web_fields = "lmid", "dev_host_id", "prod_host_id", "domain",
        zones = {}

        for w in webs:
            web = dict(zip(web_fields, w))
            zone_name = ".".join(web.get("domain").split(".")[-2:])

            if zone_name not in utils.get_keys(zones):
                zones[zone_name] = []

            zones[zone_name].append(web)

        conf_local = ""
        for zone_name in utils.get_keys(zones):
            zone = zones.get(zone_name)
            domain_records = ""
            subdomain_records = ""

            conf_local += utils.format_tpl("dns/local.tpl", {"domain": zone_name})

            for web in zone:
                prod_host_ip = dima.pools.get(web.get("prod_host_id")).ip
                dev_host_ip = dima.pools.get(web.get("dev_host_id")).ip

                if web.get("domain") == zone_name:
                    domain_records = '\n'.join([
                        "@ IN A " + prod_host_ip,
                        "www IN A " + prod_host_ip,
                        "dev IN A " + dev_host_ip,
                        "www.dev IN A " + dev_host_ip
                        ])

                else:
                    subdomain_name = web.get("domain").replace("." + zone_name, "")
                    subdomain_records += '\n'.join([
                        f"{subdomain_name} IN A {prod_host_ip}",
                        f"www.{subdomain_name} IN A {prod_host_ip}",
                        f"dev.{subdomain_name} IN A {dev_host_ip}",
                        f"www.dev.{subdomain_name} IN A {dev_host_ip}",
                        ])

            zone_conf = utils.format_tpl("dns/zone.tpl", {
                "serial": int(time.time()),
                "dns_domain": "lucamatei.net",
                "dns_ip": self.ip,
                "mail_domain": "lucamatei.net",
                "prod_host_ip": prod_host_ip,
                "domain_records": domain_records,
                "subdomain_records": subdomain_records,
                })

            utils.write("/etc/bind/db." + zone_name, zone_conf, owner="root:bind", host=self.lmid)

        # /etc/bind/named.conf.local
        utils.write("/etc/bind/named.conf.local", conf_local, owner="root:bind", host=self.lmid)

        log(f"Configured DNS server on {self.lmid} ...", console=True)

        self.restart_dns()

    @authorize
    def enable_dns(self):
        self.manage_service("enable", "bind9")

    @authorize
    def disable_dns(self):
        self.manage_service("disable", "bind9")

    @authorize
    def start_dns(self):
        self.manage_service("start", "bind9")

    @authorize
    def stop_dns(self):
        self.manage_service("stop", "bind9")

    @authorize
    def restart_dns(self):
        self.manage_service("restart", "bind9")

    @authorize
    def status_dns(self):
        self.manage_service("status", "bind9")

    # Firewall
    @authorize
    def knock(self):
        for port in self.knock_seq:
            cmd(f"sudo nmap -p {port} {self.ip}")

    @authorize
    def generate_knock_seq(self):
        log(f"Generating new port knocking sequence for '{self.name} ...'", console=True)
        self.knock_seq = []
        for i in range(4):
            self.knock_seq.append(self.next_port(True))

        query = "update host.hosts set knock_seq=%s where lmobj=%s;"
        params = self.knock_seq, self.dbid,
        dima.db.execute(query, params)

        log(f"Generated port knocking sequence for '{self.name}'", console=True)
        print(self.knock_seq)

    @authorize
    def reset_knock(self):
        self.last_knock = datetime(1945, 5, 8)

    @authorize
    def config_firewall(self):
        if "firewall" not in self.services:
            log(f"Host '{self.name}' isn't supposed to have a firewall!", level=4, console=True)
            return

        log(f"Configuring Firewall for '{self.name}' ...", console=True)
        self.manage_service("enable", "nftables")

        if not utils.isfile("/etc/nft/", host=self.lmid):
            cmd("sudo mkdir /etc/nft/", host=self.lmid)

        if "ssh_server" in self.services or "db" in self.services:
            if not self.knock_seq:
                self.generate_knock()

            knocking_rules = [f"tcp dport {self.knock_seq[0]} add @candidates {{ip saddr . {self.knock_seq[1]} timeout 1s}}"]

            for i in range(1, len(self.knock_seq)-1):
                knocking_rules.append(f"tcp dport {self.knock_seq[i]} ip saddr . tcp dport @candidates add @candidates {{ip saddr . {self.knock_seq[i+1]} timeout 1s}}")

            knocking_rules.append(f'tcp dport {self.knock_seq[-1]} ip saddr . tcp dport @candidates add @clients {{ip saddr timeout {utils.hosts.knock_grace}s}} log prefix "[nftables] Successful Port Knocking: "')

            knocking_rules = ('\n' + 8*' ').join(knocking_rules)
        else:
            knocking_rules = ""


        rule_tpls = utils.read(dima.tpls_dir + "nftables/rules.ast")
        custom_rules = [rule_tpls.get(s) for s in ("web", "dns", "ssh_server", "db") if s in self.services]
        custom_rules = utils.format_tpl(('\n' + 8*' ').join(custom_rules), {
            "ssh_port": self.ssh_port,
            "pg_port": self.pg_port,
            })

        nftables_conf = utils.format_tpl("nftables/nftables.tpl", {
            "iface": self.get_iface(),
            "knock": knocking_rules,
            "service_rules": custom_rules,
            })

        utils.write("/etc/nftables.conf", nftables_conf, host=self.lmid)
        self.send_file(dima.tpls_dir + "nftables/bogons-ipv4.tpl", "/etc/nft/bogons-ipv4.nft")
        self.send_file(dima.tpls_dir + "nftables/black-ipv4.tpl", "/etc/nft/black-ipv4.nft")
        self.manage_service("restart", "nftables")
        self.reset_knock()

        log(f"Configured Firewall for '{self.name}'", console=True)

    @authorize
    def enable_firewall(self):
        self.manage_service("enable", "nftables")

    @authorize
    def disable_firewall(self):
        self.manage_service("disable", "nftables")

    @authorize
    def start_firewall(self):
        self.manage_service("start", "nftables")

    @authorize
    def stop_firewall(self):
        self.manage_service("stop", "nftables")

    @authorize
    def restart_firewall(self):
        self.manage_service("restart", "nftables")

    # Nginx
    @authorize
    def config_nginx(self):
        if "web" not in self.services:
            log(f"Host '{self.name}' isn't a web server!", level=4, console=True)
            return

        log(f"Configuring Nginx for '{self.name}' ...")
        self.send_file(dima.tpls_dir + "web/nginx.tpl", "/etc/nginx/nginx.conf")
        cmd("sudo rm /etc/nginx/sites-enabled/default", host=self.name)
        self.manage_service("restart", "nginx")

    @authorize
    def reload_nginx(self):
        self.manage_service("reload", "nginx")

    @authorize
    def start_nginx(self):
        self.manage_service("start", "nginx")

    @authorize
    def stop_nginx(self):
        self.manage_service("stop", "nginx")

    @authorize
    def restart_nginx(self):
        self.manage_service("restart", "nginx")

    @authorize
    def status_nginx(self):
        self.manage_service("status", "nginx")

    # Postgres
    @authorize
    def create_pg_role(self, role:'str', password:'str'=None):
        # https://www.postgresql.org/docs/current/sql-createrole.html
        log(f"Creating '{role}' Postgres role on '{self.name}' ...", console=True)
        if not password:
            password = utils.new_pass(64)

        role_query = utils.dbs.query.format(f"create role {role} with login password '{password}';")
        output = cmd(role_query, catch=True, host=self.lmid)
        if "already exists" in output:
            if utils.confirm(f"'{role}' role already exists on '{self.name}'! Purge it?"):
                cmd(utils.dbs.query.format(f"drop database if exists {role};"), host=self.lmid)
                cmd(utils.dbs.query.format(f"drop role if exists {role};"), host=self.lmid)
            else: return

            cmd(role_query, host=self.lmid)

        cmd(utils.dbs.query.format(f"grant {role} to dima;"), host=self.lmid)
        self.reset_pg_pass(role, password)

        log(f"Postgres role '{role}' created on '{self.name}'", console=True)

    @authorize
    def reset_pg_pass(self, role:'str', password:'str'=None):
        log(f"Resetting database password for '{role}' on '{self.name}' ...", console=True)
        if not password:
            password = utils.new_pass(64)

        cmd(utils.dbs.query.format(f"alter role {role} with password '{password}';"), host=self.lmid)

        if role.startswith("lm"):
            utils.write(utils.projects_dir + role + "/src/app/db/db_pass.txt", password, host=self.lmid)
            return password

        else:
            utils.write(utils.tmp_dir + "db_pass.txt.tmp", password)
            log(f"Password stored in {utils.tmp_dir}db_pass.txt.tmp!", console=True)


    @authorize
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

    @authorize
    def config_postgres(self):
        """
        Manages /etc/postgresql/13/main/postgresql.conf
                /etc/postgresql/13/main/pg_hba.conf
        Assigns a new port to the PostgreSQL server.
        """

        if "db" not in self.services:
            log(f"Host '{self.name}' isn't a database server!", level=4, console=True)
            return

        log(f"Configuring PostgreSQL for '{self.name}' ...", console=True)

        pg_dir = f"/etc/postgresql/{self.pg_version}/main/"
        config_file = pg_dir + "postgresql.conf"
        hba_file = pg_dir + "pg_hba.conf"

        # Create backup for default configs
        for cfg_file in (config_file, hba_file):
            if not utils.isfile(cfg_file + ".bak", host=self.lmid):
                utils.copy(cfg_file, cfg_file + ".bak", owner="postgres:postgres", host=self.lmid)

        if self.pg_port == 5432 or utils.confirm(f"There's already a Postgres port configured for '{self.name}'! Change it?"):
            port = self.next_port(service=True)
            self.pg_port = port

            dima.db.execute("update host.hosts set pg_port=%s where lmobj=%s;", (port, self.dbid))

            log(f"Assigned new Postgres port to '{self.name}'", console=True)
            print(port)

        else:
            port = self.pg_port

        # Modify port in config file
        config = utils.format_tpl("pg/postgresql.tpl", {
            "listen": "" if self.dbid == dima.host_dbid else "," + self.ip,
            "port": port
            })

        # Allow remote access
        hba = utils.format_tpl("pg/pg_hba.tpl", {
            "remote_auth": "" if self.dbid == dima.host_dbid else f"host all all {dima.pools.get(dima.host_dbid).ip}/32 scram-sha-256"
            })

        # Write new config file and restart service
        utils.write(config_file, config, owner="postgres:postgres", tpl=True, host=self.lmid)
        utils.write(hba_file, hba, owner="postgres:postgres", tpl=True, host=self.lmid)

        # Update ports in dima projects and in db
        utils.write(utils.dbs.port_file, str(port), host=self.lmid)
        self.manage_service("restart", "postgresql")

        query = utils.dbs.query.replace("dima", "postgres")
        has_db = cmd(query.format(f"select 1 from pg_database where datname='dima';"), catch=True, host=self.lmid)

        if not has_db:
            cmd(query.format(f"create role dima with login createdb createrole password '{utils.new_pass(64)}';"), host=self.lmid)
            cmd(query.format("create database dima owner dima encoding 'utf-8';"), host=self.lmid)

        log(f"Configured PostgreSQL for '{self.name}'", console=True)

    @authorize
    def reload_postgres(self):
        self.manage_service("reload", "postgresql")

    @authorize
    def start_postgres(self):
        self.manage_service("start", "postgresql")

    @authorize
    def stop_postgres(self):
        self.manage_service("stop", "postgresql")

    @authorize
    def restart_postgres(self):
        self.manage_service("restart", "postgresql")

    @authorize
    def status_postgres(self):
        self.manage_service("status", "postgresql")

    # Supervisor
    @authorize
    def start_supervisor(self):
        self.manage_service("start", "supervisor")

    @authorize
    def stop_supervisor(self):
        self.manage_service("stop", "supervisor")

    @authorize
    def restart_supervisor(self):
        self.manage_service("restart", "supervisor")

    @authorize
    def status_supervisor(self):
        self.manage_service("status", "supervisor")

    # SSH
    @authorize
    def restart_ssh(self):
        self.manage_service("restart", "ssh")

    @authorize
    def config_ssh_client(self):
        if "ssh_client" not in self.services:
            log(f"Host '{self.name}' isn't a SSH client!", level=4, console=True)
            return

        log(f"Configuring SSH Client for '{self.name}' ...", console=True)

        if not utils.isfile("/home/dima/.ssh/", host=self.lmid):
            cmd("mkdir /home/dima/.ssh/", host=self.lmid)
        cmd("chmod 700 /home/dima/.ssh/", host=self.lmid)

        hosts = []

        if self.dbid == dima.host_dbid:
            query = "select a.lmid, a.alias, b.ip, b.ssh_port from lmobjs a, host.hosts b where a.id = b.lmobj and a.id != %s;"
            params = dima.host_dbid,

            for host in dima.db.execute(query, params):
                hosts.append(utils.format_tpl("ssh/host.tpl", {
                    "lmid": host[0],
                    "ip": host[2],
                    "port": host[3],
                    "user": "dima",
                    "privkey": utils.ssh_dir + host[0],
                    }))

                if host[1]:
                    hosts.append(utils.format_tpl("ssh/host.tpl", {
                        "lmid": host[1],
                        "ip": host[2],
                        "port": host[3],
                        "user": "dima",
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

        utils.write("/home/dima/.ssh/config", hosts, tpl=True, host=self.lmid)
        self.update_hosts_file()

        log(f"Configured SSH Client for '{self.name}'", console=True)

    @authorize
    def config_ssh_server(self):
        if "ssh_server" not in self.services:
            log(f"Host '{self.name}' isn't a SSH server!", level=4, console=True)
            return

        log(f"Configuring SSH Server for '{self.name}' ...", console=True)

        cmd("sudo groupadd sshusers", host=self.lmid)
        cmd("sudo usermod -a -G sshusers dima", host=self.lmid)

        if self.ssh_port == 22 or utils.confirm(f"There's already a SSH port configured for '{self.name}'! Change it?"):
            port = self.next_port(service=True)

            dima.db.execute("update host.hosts set ssh_port=%s where lmobj=%s;", (port, self.dbid))

            log(f"Assigned new SSH port to '{self.name}'", console=True)
            print(port)

        else:
            port = self.ssh_port

        config = utils.format_tpl("ssh/server_config.tpl", {
            "port": port,
            })

        utils.write("/etc/ssh/sshd_config", config, tpl=True, host=self.lmid)
        #self.config_firewall()
        self.restart_ssh()

        self.ssh_port = port
        dima.pools.get(dima.host_dbid).config_ssh_client()

        log(f"Configured SSH Server for '{self.name}'", console=True)

    @authorize
    def create_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Generating SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'. This may take a while ...", console=True)

        host = self.lmid if for_gitlab else dima.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        if utils.isfile(privkey, host=host):
            if utils.confirm(f"SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}' already exists! Overwrite it?"):
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(ssh.keygen.format(privkey), host=host)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)

            log(f"SSH Key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}' generated", console=True)

            log(f"\nUse the following command to copy the key manually. Beware of the user name.\n$ ssh-copy-id -i {privkey}.pub dima@{self.ip}\n", console=True)

            if for_gitlab:
                self.config_ssh_client()
                gitlab.add_ssh_key(self.lmid, utils.read(utils.ssh_dir + self.lmid + "-gitlab.pub", host=self.lmid))
            else:
                dima.pools.get(dima.host_dbid).config_ssh_client()

            return 1
        else:
            log(f"Couldn't generate SSH key to access {'Gitlab from ' if for_gitlab else ''}host '{self.name}'!", level=4, console=True)

            return 0

    @authorize
    def delete_ssh_key(self, for_gitlab:'bool'=False):
        log(f"Removing {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}' ...", console=True)

        host = self.lmid if for_gitlab else dima.host_lmid
        privkey = utils.ssh_dir + self.lmid + ("-gitlab" if for_gitlab else '')

        cmd(f"rm {privkey} {privkey}.pub", host=host)

        log(f"Removed {'Gitlab ' if for_gitlab else ''}SSH key for host '{self.name}'", console=True)

    ## GPG
    @authorize
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

    @authorize
    def get_gpg_key_id(self, email:'str'=None):
        if not email: email = self.email
        key_id = cmd(f"gpg2 --list-keys --keyid-format LONG {email}", catch=True, host=self.lmid)

        if "No public key" in key_id:
            if utils.confirm(f"Couldn't find GPG key for '{email}'! Create one?"):
                return self.create_gpg_key(email)
            return 0
        else:
            return re.findall(r'\bpub   rsa4096/\w+', key_id)[0].split('/')[1]

    @authorize
    def create_gpg_key(self, email:'str'=None):
        if self.env != "dev":
            log(f"'{self.name}' isn't a development machine!", level=4, console=True)
            return

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

    @authorize
    def delete_gpg_key(self, email:'str'=None):
        if self.env != "dev":
            log(f"'{self.name}' isn't a development machine!", level=4, console=True)
            return

        log(f"Removing GPG Key for '{email}' ...", level=3, console=True)
        if not email: email = self.email
        cmd(f"gpg2 --batch --delete-secret-keys {email}", host=self.lmid)
        cmd(f"gpg2 --batch --delete-keys {email}", host=self.lmid)
        log(f"Removed GPG key for '{email}'!", level=3, console=True)


class Host(lmObj, HostServices):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        """
            Prepare VPS

            # apt update && apt upgrade -y

            # nano /etc/hostname
            # nano /etc/hosts

            # adduser --gecos '' dima
            # sudo -u dima mkdir /home/dima/.ssh/
            # chmod 700 /home/dima/.ssh/
            # sudo -u dima nano /home/dima/.ssh/authorized_keys
            # chmod 600 /home/dima/.ssh/authorized_keys

            # echo "dima ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/dima

            # nano /etc/ssh/sshd_config
            # systemctl restart ssh
            # systemctl reboot
        """

        query = "select mac, net, ip, client, env, knock_seq, ssh_port, pg_port, pm, services from host.hosts where lmobj=%s;"
        params = dbid,

        self.mac, self.net_id, self.ip, self.client_id, self.env_id, self.knock_seq, self.ssh_port, self.pg_port, self.pm_id, self.service_ids = dima.db.execute(query, params)[0]

        self.env = utils.hosts.envs.get(self.env_id)
        self.mnt_dir = utils.mnt_dir + self.name + "/"
        self.services = [utils.hosts.services.get(x) for x in self.service_ids]
        self.email = self.lmid + "@" + utils.hosts.domain

        self.reset_knock()

    @authorize
    def next_port(self, service:'bool'=False):
        if service:
            min, max = 4096, 8192
            used = [self.ssh_port, self.pg_port, 5432, 8080, 4343, 5353] + self.ssh_knock

        else:
            min, max = 16384, 32768
            used = []
            for ports in dima.db.execute("select a.dev_port, a.prod_port, b.port from web.webs a, project.apps b;"):
                used.extend(ports)

        port = random.randint(min, max)

        while port in used:
            port = random.randint(min, max)

        return port

    @authorize
    def has_storage(self, capacity):
        return True

    # Projects
    @authorize
    def create_project(self, lmid, module, alias, name, description):
        if gitlab.create_project(data={
            'path': lmid,
            'name': name,
            'description': description,
            'visibility': 'private',
            'initialize_with_readme': True,
            }):

            dbid = dima.insert_lmobj(lmid, module, alias)

            query = f"insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = dbid, self.dbid, 0.1, self.dbid, 0.1, name, description,
            dima.db.execute(query, params)

            self.clone_repo(lmid)
            return dbid

        return 0

    @authorize
    def clone_repo(self, path:'str'):
        log(f"Cloning '{path}' Gitlab repository ...", console=True)
        cmd(f"git clone git@{gitlab.domain}:{gitlab.user}/{path}.git {utils.projects_dir}{path}/", host=self.lmid)
        log(f"'{path}' cloned", console=True)

    # Web
    @authorize
    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=("static",), langs:'list'=("en",), themes:'list'=("light",), default_lang:'str'="en", default_theme:'str'="light", has_animations:'bool'=False):

        # To do: validate parameters

        #if dima.domains.get(domain):
            #log("Domain already exists!", level=4, console=True)
            #return 0

        lmid = dima.next_lmid()
        dbid = self.create_project(lmid, "Web", alias, name, description)

        if dbid:
            module_ids = [x for x in [utils.webs.modules.get(m, 0) for m in modules] if x]
            lang_ids = [x for x in [utils.projects.langs.get(l, 0) for l in langs] if x]
            theme_ids = [x for x in [utils.projects.themes.get(t, 0) for t in themes] if x]

            query = "insert into web.webs (lmobj, domain, dev_port, prod_port, dev_ssl_due, prod_ssl_due, prod_state, modules, langs, themes, default_lang, default_theme, has_animations) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id;"
            params = dima.lmobjs[lmid], domain, self.next_port(), self.next_port(), None, None, 0, module_ids, lang_ids, theme_ids, utils.projects.langs[default_lang], utils.projects.themes[default_theme], has_animations,

            if dima.db.execute(query, params)[0][0]:
                log(f"{name if name else (alias if alias else lmid)} web app created!", console=True)
                dima.create_pool(dbid)
                self.update_hosts_file()
                return 1

        log(f"Couldn't create web app '{lmid}'!", level=4, console=True)

    @authorize
    def generate_dh(self):
        if utils.isfile(utils.ssl_dir + "dhparam.pem", host=self.lmid):
            if utils.confirm("DH parameters are already in place! Purge them?"):
                cmd(f"sudo rm {utils.ssl_dir}dhparam.pem", host=self.lmid)
            else:
                return

        log(f"Generating DH params for '{self.name}'. This may take a while ...", console=True)
        cmd(f"sudo openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096", host=self.lmid)
        log(f"Generated DH params for '{self.name}'", console=True)

    # Hosts
    @authorize
    def create_host(self, env:'str'="dev", alias:'str'=None, mem:'int'=1024, cpus:'int'=1, disk:'int'=5):
        lmid = dima.next_lmid()
        log(f"Creating new '{lmid}' VM ...", console=True)

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

            dbid = dima.insert_lmobj(lmid, 'Host', alias)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = dbid, mac, self.net_id, ip, None, utils.hosts.envs.get(env), ssh_port, self.next_port(service=True), self.dbid,

            dima.db.execute(query, params)
            dima.pools.get(dima.host_dbid).config_ssh_client()

            log(f"'{lmid}' VM created on '{self.name}'", console=True)
            dima.create_pool(dbid)

        else:
            log(f"Couldn't create '{lmid}' VM on '{self.name}'!", level=4, console=True)

    # Mount
    @authorize
    def is_mounted(self):
        if len(os.listdir(self.mnt_dir)):
            return True
        return False

    @authorize
    def mount(self):
        if self.dbid == dima.host_dbid:
            log("You can't mount the host!", level=4, console=True)
        else:
            if not utils.isfile(self.mnt_dir):
                log(f"Creating mount point at '{self.mnt_dir}' ...")
                cmd("mkdir " + self.mnt_dir)

            if not self.is_mounted():
                cmd(f"sshfs -p {self.ssh_port} -o allow_other,identityfile={utils.ssh_dir}{self.lmid} dima@{self.ip}:/home/dima {self.mnt_dir}")
                log(f"'{self.name}' mounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already mounted!", level=4, console=True)

    @authorize
    def unmount(self):
        if self.dbid == dima.host_dbid:
            log("You can't unmount the host!", level=4, console=True)
        else:
            if self.is_mounted():
                cmd(f"fusermount -u {self.mnt_dir}")
                log(f"'{self.name}' unmounted at {utils.now()}", console=True)
            else:
                log(f"'{self.name}' is already unmounted!", level=4, console=True)

    # System
    @authorize
    def config_sysctl(self):
        log(f"Configuring sysctl for '{self.name}' ...", console=True)
        sysctl = utils.format_tpl("sysctl.tpl", {
            "iface": self.get_iface()
            })
        utils.write("/etc/sysctl.conf", sysctl, tpl=True, host=self.lmid)
        cmd("sudo sysctl -p", host=self.lmid)
        log(f"Configured sysctl for '{self.name}'", console=True)

    @authorize
    def config_grub(self):
        log(f"Configuring GRUB for '{self.name}' ...", console=True)
        self.send_file(dima.tpls_dir + "grub.tpl", "/etc/default/grub")
        cmd("sudo update-grub", host=self.lmid)
        log(f"Configured GRUB for '{self.name}'", console=True)

    @authorize
    def config_motd(self):
        self.send_file(dima.tpls_dir + "motd.tpl", "/etc/motd")

    @authorize
    def update_resources(self):
        log(f"Updating resources for '{self.name}' ...", console=True)
        if self.dbid != dima.host_dbid:
            cmd(f"rm -r {utils.res_dir}web/", host=self.lmid)
            self.send_file(utils.res_dir + "web/", utils.res_dir + "web/")
        else:
            # Download resources
            pass
        log(f"Updated resources for '{self.name}'", console=True)

    @authorize
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

        if self.dbid == dima.host_dbid:
            # Hosts
            query = "select a.ip, b.lmid, b.alias from host.hosts a, lmobjs b where b.id = a.lmobj and b.id != %s;"
            params = self.dbid,
            db_hosts = [list(h) for h in dima.db.execute(query, params)]

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
            db_webs = [list(h) for h in dima.db.execute(query, params)]

            for web in db_webs:
                append_web(web)
        else:
            host_entries = ""
            query = "select a.ip, b.ip, c.name, d.lmid from host.hosts a, host.hosts b, domains c, lmobjs d, web.webs e, project.projects f where a.lmobj = f.prod_host and b.lmobj = f.dev_host and c.id = e.domain and d.id = e.lmobj and d.id = f.lmobj and c.name=%s;"
            #params = utils.webs.assets_domain,
            #web = list(dima.db.execute(query, params)[0])

            #append_web(web)

        web_entries = "\n".join(hosts)

        hosts_file = utils.format_tpl("hosts.tpl", {
            "host": host_entry,
            "hosts": "", #host_entries,
            "webs": "", #web_entries
            })
        utils.write("/etc/hosts", hosts_file, host=self.lmid)

        log(f"Generated /etc/hosts for '{self.name}'", console=True)

    @authorize
    def set_permissions(self):
        # All  -rw-rw-r--
        cmd("sudo chmod g+w -R /home/dima/", host=self.lmid)

        # /home/dima/.ssh/config  -rw-r--r--
        cmd("sudo chmod g-w /home/dima/.ssh/config", host=self.lmid)

        # /home/dima/ssh/  -rw-------
        cmd("sudo chmod 600 /home/dima/ssh/*", host=self.lmid)

        # personal_token.txt  -rw-------
        if self.dbid == dima.host_dbid: cmd("sudo chmod 600 /home/dima/lm1/src/app/personal_token.txt")

        # project_token.txt, db_pass.txt  -rw-------
        for prjct_dir in utils.get_dirs("/home/dima/projects/"):
            if prjct_dir.endswith(("pids/", "venv/")):
                continue

            if utils.isfile(prjct_dir + "project_token.txt", host=self.lmid):
                cmd(f"sudo chmod 600 {prjct_dir}project_token.txt", host=self.lmid)

            if utils.isfile(prjct_dir + "src/app/db/db_pass.txt", host=self.lmid):
                cmd(f"sudo chmod 600 {prjct_dir}src/app/db/db_pass.txt", host=self.lmid)

    @authorize
    def install_dependencies(self):
        packages = "libpam-cracklib", "build-essential", "python3", "python3-dev", "python3-venv", "python3-pip",

        log(f"Installing dependencies on '{self.name}' ...", console=True)

        if self.env == "dev":
            packages += "gnupg2", "git", "curl"

        if "web" in self.services:
            packages += "openssl", "nginx", "supervisor",

        if "web" in self.services or "db" in self.services:
            packages += "postgresql", "libpq-dev",

        if "ssh_server" in self.services:
            packages += "openssh-server",

        if "ssh_client" in self.services:
            packages += "openssh-client",

        if "vms" in self.services:
            packages += "bridge-utils",

        if "dhcp" in self.services:
            packages += "isc-dhcp-server",

        if "dns" in self.services:
            packages += "bind9", "bind9utils"

        if "firewall" in self.services:
            pass
            #packages += "nftables",

        if "mail" in self.services:
            packages += "postfix",

        for package in packages:
            if not "ok installed" in cmd(f"sudo dpkg -s {package} | grep Status", catch=True, host=self.lmid):
                log(f"Installing '{package}' ...", console=True)
                cmd(f"sudo apt install {package} -y", catch=True, host=self.lmid)
            else:
                log(f"'{package}' is already installed!", console=True)

        log(f"Installed dependencies on '{self.name}' ...", console=True)

    @authorize
    def create_user(self, name:'str'):
        # https://manpages.debian.org/jessie/adduser/adduser.8.en.html
        if not cmd(f"getent passwd {name}", catch=True):
            log(f"Creating user and group '{name}' ...", console=True)

            cmd(f"sudo adduser --group --gecos '' {name}", catch=True)
            cmd(f"sudo echo {name}:{utils.new_pass(64)} | sudo chpasswd")

            log(f"Created user and group '{name}'", console=True)
        else:
            if not utils.confirm(f"User '{name}' already exists! Use it?"):
                log(f"Can't create another user '{name}'!", level=4, console=True)

    @authorize
    def ping(self):
        log(f"Trying to ping '{self.name}' ...", console=True)
        if self.dbid == dima.host_dbid:
            print("It's this machine, dumbass!")
        else:
            response = cmd("echo 1", catch=True, host=self.lmid)
            if response == "1":
                log(f"Host '{self.name}' reached!", console=True)
                return 1
            else:
                log(f"Couldn't reach host '{self.name}'!", level=3, console=True)
                return 0

    @authorize
    def build_dir_tree(self):
        log(f"Creating Dima's directory tree on '{self.name}' ...", console=True)

        dir_tree = [
            utils.logs_dir,
            utils.projects_dir,
                utils.projects_dir + "pids/",
            utils.tmp_dir
            ]

        if "vms" in self.services:
            dir_tree.extend([utils.vms_dir])

        if "ssh_client" in self.services:
            dir_tree.extend([utils.ssh_dir])

        if self.dbid == dima.host_dbid:
            dir_tree.extend([
                utils.res_dir,
                    utils.res_dir + "web/",
                    utils.res_dir + "web/css/",
                    utils.res_dir + "web/js/",
                    utils.res_dir + "web/fonts/",
                    utils.res_dir + "web/icons/",
            ])

        utils.create_dir_tree(dir_tree, host=self.lmid)

        if "web" in self.services:
            if not utils.isfile(utils.ssl_dir, host=self.lmid):
                cmd(f"sudo mkdir {utils.ssl_dir}", host=self.lmid)

        cmd(f"sudo chown www-data:www-data {utils.projects_dir}pids", host=self.lmid)

    @authorize
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

    @authorize
    def config_git(self):
        log(f"Configuring Git for '{self.name}' ...", console=True)

        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.lmid,
            "email": self.email,
            "gpg_key_id": self.get_gpg_key_id(self.email),
            })

        utils.write(f"/home/dima/.gitconfig", config, tpl=True, host=self.lmid)

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

    @authorize
    def config_sudo(self, user:'str'="dima"):
        user = "dima"
        log(f"Configuring sudo for user {user} on host '{self.lmid}' ...", console=True)

        utils.write(f"{user} ALL=(ALL) NOPASSWD:ALL", f"/etc/sudoers.d/{user}", host=self.lmid)

        log(f"Configured sudo for user {user} on host '{self.lmid}'", console=True)

    @authorize
    def setup(self):
        self.install_dependencies()
        self.build_dir_tree()

        self.config_ssh_server()
        self.config_grub()
        self.config_motd()
        self.config_sysctl()

        self.build_venv()
        self.update_resources()

        if "web" in self.services:
            self.generate_dh()
            self.config_nginx()

        if "web" in self.services or "db" in self.services:
            self.config_postgres()

        if "dhcp" in self.services:
            self.config_dhcp()

        if "dns" in self.services:
            self.config_dns()

        if "firewall" in self.services:
            self.config_firewall()

        if self.env == "dev":
            self.config_git()
            self.create_ssh_key(for_gitlab=True)

    @authorize
    def has_file(self, path:'str'):
        if utils.isfile(path, host=self.lmid):
            log("File exists!", console=True)

    @authorize
    def send_file(self, src_path:'str', dest_path:'str', owner:'str'="root:root"):
        is_dir = src_path.endswith('/')

        final_path = None
        if dest_path.startswith("/etc/"):
            final_path = dest_path
            dest_path = utils.tmp_dir + 'restricted' + ('/' if is_dir else '')

        cmd(f"scp {'-r ' if is_dir else ''}-P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} {src_path.rstrip('/')} dima@{self.lmid}:{dest_path.rstrip('/')}", catch=True)

        if final_path:
            cmd(f"sudo mv {dest_path} {final_path}", host=self.lmid)
            cmd(f"sudo chown {owner} {final_path}", host=self.lmid)

    @authorize
    def retrieve_file(self, src_path:'str', dest_path:'str'):
        is_dir = src_path.endswith('/')
        # Handle permissions
        cmd(f"scp {'-r ' if is_dir else ''}-P {self.ssh_port} -o identityfile={utils.ssh_dir}{self.lmid} dima@{self.lmid}:{src_path.rstrip('/')} {dest_path.rstrip('/')}", catch=True)

    @authorize
    def rebuild(self):
        pass

    @authorize
    def status(self):
        print("OK")

    @authorize
    def update(self):
        log(f"Updating '{self.name}' ...", console=True)
        cmd("sudo apt update && sudo apt upgrade -y", host=self.lmid)
        log(f"Updated '{self.name}'", console=True)

    @authorize
    def reboot(self):
        log(f"Rebooting '{self.name}' ...", console=True)
        cmd("sudo systemctl reboot", host=self.lmid)

        for i in range(1, 4):
            log(f"Waiting for 4 seconds...", console=True)
            time.sleep(4)
            log(f"Ping try #{i}", console=True)

            if self.ping():
                log(f"Rebooted '{self.name}'", console=True)
                return

        log(f"Lost connection with machine!", level=4, console=True)
        task.abort()

    @authorize
    def test(self):
        log("TEST", console=True)

    @authorize
    def check(self):
        if not self.knock_seq:
            self.generate_knock()
