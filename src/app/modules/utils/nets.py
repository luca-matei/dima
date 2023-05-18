class NetUtils:
    zones = {}

    def get_zone(self, domain:'str'):
        return '.'.join(domain.split(".")[-2:])

    def in_subnets(self):
        subnets = []

        for x in cmd("ip a", catch=True).split(' '):
           if x.startswith(('192.168.', '172.16.', '10.')) and '/' in x:
               subnets.append(x)

        return subnets

utils.nets = NetUtils()
