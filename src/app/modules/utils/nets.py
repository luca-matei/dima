class NetUtils:
    def in_subnets(self):
        subnets = []

        for x in cmd("ip a", catch=True).split(' '):
           if x.startswith(('192.168.', '172.16.', '10.')) and '/' in x:
               subnets.append(x)

        return subnets

    def set_dhcp(self):
        # To do: nmap scan, display available hosts, make install script for one
        pass

utils.nets = NetUtils()
