class lmObj:
    def __init__(self, dbid):
        self.dbid = dbid
        self.lmid = hal.lmobjs[dbid][0]
        self.alias = hal.lmobjs[dbid][2]
        self.name = self.alias if self.alias else self.lmid

    def set_alias(self, alias):
        forbidden = "", "q", "exit"

        if alias in forbidden or alias.startswith("lm") or alias in utils.get_keys(cli.acts):
            log("Can't assign this alias!", level=4, console=True)

        elif alias in utils.get_keys(hal.lmobjs):
            log(f"Alias already in use by {hal.lmobjs[hal.lmobjs[alias]][0]}!", level=4, console=True)

        else:
            hal.lmobjs.pop(self.alias, None)
            hal.lmobjs[alias] = self.dbid
            self.alias = alias

            hal.db.execute("update lmobjs set alias=%s where id=%s;", (alias, self.dbid,))
            log(f"Alias '{alias}' set to {self.lmid}.", console=True)

    def remove_alias(self):
        hal.lmobjs.pop(self.alias, None)
        self.alias = None
        hal.db.execute("update lmobjs set alias=%s where id=%s;", (None, self.dbid,))
        log("Alias removed.", console=True)
