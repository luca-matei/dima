
class DNS(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        query = "select glue, master, slaves from net.dnss where lmobj=%s;"
        params = self.dbid,
        self.glue, self.master_id, self.slave_ids = dima.db.execute(query, params)[0]
