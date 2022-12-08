class Net:
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, domain, gateway, lease_start, lease_end from nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.domain, self.gateway, self.lease_start, self.lease_end = hal.db.execute(query, params)[0]

        #self.check()

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

    def autostart(self):
        """
        :public
        Toggles autostart flag.
        """

        if self.dbid != hal.net_dbid:
            autolaunch = False if self.autolaunch else True
            out = cmd(f"sudo virsh net-autostart {'' if autolaunch else '--disable '}" + self.lmid, catch=True)
            if (autolaunch and f"Network {self.lmid} marked as autostarted" in out) or (not autolaunch and f"Network {self.lmid} unmarked as autostarted" in out):
                self.autolaunch = autolaunch
                hal.db.execute("update nets set autolaunch=%s where lmobj=%s;", (self.autolaunch, self.dbid,))
                log(f"{'Added' if self.autolaunch else 'Removed'} autostart flag for {self.lmid} net.", console=True)
                return 1

        log(f"Couldn't toggle 'autostart' flag for {self.lmid} net!", level=4, console=True)
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

    def check(self):
        if self.dbid != hal.net_dbid:
            if not util.isfile(f"/etc/libvirt/qemu/networks/{self.lmid}.xml"):
                if hal.nutil.create_libvirt_net(self.lmid, self.netmask, self.gateway):
                    self.start()
                    self.autostart()
                    hal.nutil.config_dhcp()
