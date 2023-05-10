
class Domain:
    def __init__(self, dbid):
        self.dbid = dbid

        query = "select name, ssl_due, dhcp, dns, mail from domains where id=%s;"
        params = self.dbid,
        self.name, self.ssl_due, self.dhcp_id, self.dns_id, self.mail_id = dima.db.execute(query, params)[0]

        self.dhcp = None
        self.dns = None
        self.mail = None

        if not self.name.startswith("dev."):
            try:
                self.dev = dima.domains.get(dima.domains.get("dev." + self.name))
            except:
                self.dev = None
        else:
            self.dev = None
