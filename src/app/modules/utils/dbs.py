class DbUtils:
    query = """sudo -u hal psql -tAc \"{}\""""

    def create_pgrole(self, lmid):
        log(f"Creating {lmid} role ...", console=True)
        password = utils.new_pass(64)

        if lmid == "hal":
            query = self.query.replace("hal", "postgres")
        else:
            query = self.query

        role_query = query.format(f"create role {lmid} with login password '{password}';")
        output = cmd(role_query, catch=True)
        if "already exists" in output:
            log(f"{lmid} role already exists!", console=True)
            yes = utils.yes_no("Purge it?")

            if yes: cmd(query.format(f"drop database {lmid} if exists; drop role {lmid};"))
            else: return

            cmd(role_query)

        if lmid == "hal":
            return

        elif lmid.startswith("lm"):
            settings_path = utils.projects_dir + lmid + "/src/app/settings.ast"
            settings = utils.read(settings_path)
            settings['db_pass'] = password
            utils.write(settings_path, settings)
            return password

        else:
            log(f"Password stored in {utils.tmp_dir}db_pass.tmp!", console=True)
            utils.write(utils.tmp_dir + "db_pass.tmp", password)

    def create_pgdb(self, lmid):
        log(f"Creating {lmid} database ...", console=True)
        db_query = self.query.format(f"create database {lmid} owner {lmid} encoding 'utf-8';")
        output = cmd(db_query, catch=True)
        if "already exists" in output:
            log(f"{lmid} database already exists!", console=True)
            yes = utils.yes_no("Purge it?")

            if yes: cmd(self.query.format(f"drop database {lmid};"))
            else: return

            cmd(db_query, catch=True)

utils.dbs = DbUtils()
