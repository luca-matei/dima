class NetUtils:
    def in_subnets(self):
        subnets = []

        for x in cmd("ip a", catch=True).split(' '):
           if x.startswith(('192.168.', '172.16.', '10.')) and '/' in x:
               subnets.append(x)

        return subnets

    def get_free_ip(self, net_id):
        # This is not bound to a Net because I'll need a free ip on specific nets

        # Get machine's ips
        query = "select ip from host.hosts where net=%s;"
        params = net_id,
        used_ips = dima.db.execute(query, params)

        if used_ips:
            used_ips = [ipaddress.ip_address(ip[0]) for ip in used_ips]

        query = "select netmask, gateway, lease_start, lease_end from nets where lmobj=%s;"
        netmask, gateway, lease_start, lease_end = dima.db.execute(query, params)[0]

        net = ipaddress.ip_network(gateway + '/' + netmask, strict=False)
        lease_start = ipaddress.ip_address(lease_start)
        lease_end = ipaddress.ip_address(lease_end)

        for ip in net.hosts():
            if ip >= lease_start and ip <= lease_end and ip not in used_ips:
                return str(ip)

        log(f"No free ips for net {dima.pools.get(net_id).name}!", level=4, console=True)
        return None

utils.nets = NetUtils()
