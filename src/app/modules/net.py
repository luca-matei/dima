class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, dhcp, dns, domain, gateway, lease_start, lease_end from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.dhcp_id, self.dns_id, self.domain_id, self.gateway, self.lease_start, self.lease_end = hal.db.execute(query, params)[0]

        self.domain = hal.domains.get(self.domain_id)

        self.check()

    def set_dhcp(self, host=None):
        def get_opt(opts, db_opts):
            for host in db_opts:
                # Display alias too
                if host[2]:
                    opts[host[0]] = f"{host[1]} ({host[2]})"
                else:
                    opts[host[0]] = host[1]

            return utils.select_opt(opts)

        opts = {
            -2: "Register a host",
            -1: "Create a VM",
            }

        query = "select id, lmid, alias from lmobjs where module=%s;"
        params = hal.modules.get("Host"),
        dhcp_id = get_opt(opts, hal.db.execute(query, params))

        # Register a host
        if dhcp_id == -2:
            utils.hosts.register_host()
            log("You have to run again this command after you've installed the new host!", level=3, console=True)
            return

        # Create a VM
        elif dhcp_id == -1:
            # Select physical machines to host the VM
            query = "select a.id, a.lmid, a.alias from lmobjs a, host.hosts b where b.lmobj=a.id and b.pm=null;"
            pm_id = get_opt({}, hal.db.execute(query))

            if pm_id:
                hal.pools.get(pm_id).create_host()
                self.set_dhcp()
                return
            else:
                log(f"Couldn't create a DHCP server for net {self.name}!", level=4, console=True)

        elif dhcp_id:
            pool = hal.pools.get(dhcp_id)
            if not pool:
                hal.create_pool(dhcp_id)
                pool = hal.pools.get(dhcp_id)

            pool.config_dhcp()
            log(f"{pool.name} set as DHCP server for net {self.name}.", console=True)

        else:
            log(f"Couldn't set a DHCP server for net {self.name}!", level=4, console=True)

    def set_dns(self, host=None):
        pass

    def check(self):
        if not self.dhcp_id:
            log(f"Net {self.name} doesn't have a DHCP server set!", level=3, console=True)
            self.set_dhcp()

        if not self.dns_id:
            log(f"Net {self.name} doesn't have a DNS set!", level=3, console=True)
            self.set_dns()
