class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, dhcp, dns, domain, gateway, lease_start, lease_end, is_virtual from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.dhcp_id, self.dns_id, self.domain, self.gateway, self.lease_start, self.lease_end, self.is_virtual = hal.db.execute(query, params)[0]

        self.check()

    def start(self):
        """
        :public
        Starts the network.
        """

        if self.dbid != hal.net_dbid:
            if f"Network {self.lmid} started" in cmd("sudo virsh net-start " + self.lmid, catch=True):
                self.state = 1
                hal.db.execute("update nets set state=%s where lmobj=%s;", (self.state, self.dbid,))
                log(f"{self.lmid} net started.", console=True)
                return 1

        log(f"Couldn't start {self.lmid} net!", level=4, console=True)
        return 0

    def stop(self):
        """
        :public
        Stops the network.
        """

        if self.dbid != hal.net_dbid:
            if f"Network {self.lmid} destroyed" in cmd("sudo virsh net-destroy " + self.lmid, catch=True):
                self.state = 0
                hal.db.execute("update nets set state=%s where lmobj=%s;", (self.state, self.dbid,))
                log(f"{self.lmid} net stopped.", console=True)
                return 1

        log(f"Couldn't stop {self.lmid} net!", level=4, console=True)
        return 0

    def delete(self):
        # To do: move guests to another net
        if self.dbid != hal.net_dbid:
            if self.stop():
                if f"Network {self.lmid} has been undefined" in cmd("sudo virsh net-undefine " + self.lmid, catch=True):
                    hal.db.execute("delete from nets where lmobj=%s;", (self.dbid,))
                    log(f"{self.lmid} net deleted.", console=True)
                    hal.nutil.config_dhcp()
                    hal.hutil.destroy_pool(self.dbid)
                    return 1

        log(f"Couldn't delete {self.lmid} net!", level=4, console=True)
        return 0

    def set_dhcp(self, host=None):
        opts = {
            -2: "Register a host",
            -1: "Create a host",
            }

        query = "select id, lmid, alias from lmobjs where module=%s;"
        params = hal.modules["Host"],

        for host in hal.db.execute(query, params):
            # Display alias too
            if host[2]:
                opts[host[0]] = f"{host[1]} ({host[2]})"
            else:
                opts[host[0]] = host[1]

        opt = utils.select_opt(opts)

        # Register new host
        if opt == -2:
            pass

        # Create new host
        elif opt == -1:
            pass

        elif opt == 0:
            log(f"Couldn't set a DHCP server for net {self.name}!", level=4, console=True)

        else:
            host = opts.get(opt)

        print(opts.get(opt))

    def set_dns(self, host=None):
        pass

    def check(self):
        if not self.dhcp_id:
            log(f"Net {self.name} doesn't have a DHCP server set!", level=3, console=True)
            self.set_dhcp()

        if not self.dns_id:
            log(f"Net {self.name} doesn't have a DNS set!", level=3, console=True)
            self.set_dns()
