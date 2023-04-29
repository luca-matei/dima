class lmObj:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = dima.lmobjs[dbid][0]
        self.alias = dima.lmobjs[dbid][2]
        self.name = self.alias if self.alias else self.lmid

    def set_alias(self, alias:'str'):
        log(f"Setting alias '{alias}' to '{self.lmid}' ...", console=True)
        if dima.check_alias(alias):
            dima.lmobjs.pop(self.alias, None)
            dima.lmobjs[alias] = self.dbid
            self.alias = alias

            dima.db.execute("update lmobjs set alias=%s where id=%s;", (alias, self.dbid,))
            log(f"Alias '{alias}' set to {self.lmid}", console=True)

    def delete_alias(self):
        log(f"Removing alias '{self.alias}' from '{self.lmid}'...", console=True)
        dima.lmobjs.pop(self.alias, None)
        self.alias = None
        dima.db.execute("update lmobjs set alias=%s where id=%s;", (None, self.dbid,))
        log("Alias deleted", console=True)
