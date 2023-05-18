class Net(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select netmask, domain, dhcp, gateway, lease_start, lease_end from net.nets where lmobj=%s;"
        params = dbid,
        self.netmask, self.domain, self.dhcp_id, self.gateway, self.lease_start, self.lease_end = dima.db.execute(query, params)[0]

        self.obj = ipaddress.ip_network(self.gateway + '/' + self.netmask, strict=False)
        self.ip = str(self.obj[0])
        self.broadcast = self.obj[-1]

        self.dns_id = utils.nets.get_zone(self.domain).get("priv_dns" if self.domain.startswith("home.") else "pub_dns")

    def get_ip(self):
        # Get machine's ips
        query = "select ip from host.hosts where net=%s;"
        params = self.dbid,
        used_ips = dima.db.execute(query, params)

        if used_ips:
            used_ips = [ipaddress.ip_address(ip[0]) for ip in used_ips]

        lease_start = ipaddress.ip_address(self.lease_start)
        lease_end = ipaddress.ip_address(self.lease_end)

        for ip in self.obj.hosts():
            if ip >= lease_start and ip <= lease_end and ip not in used_ips:
                return str(ip)

        log(f"No vacant IPs on net '{self.name}'!", level=4, console=True)
        return None

    def test(self):
        log("TEST", console=True)

    def check(self):
        if not self.dhcp_id:
            log(f"Net '{self.name}' doesn't have a DHCP server set!", level=3, console=True)
            self.set_dhcp()
