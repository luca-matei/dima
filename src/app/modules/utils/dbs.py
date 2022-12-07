class DbUtils:
    query = """sudo -u postgres psql -tAc \"{}\""""

    def create_db(self, host=None):
        pass

    def create_pgrole(self, lmid, host=None):
        # https://www.postgresql.org/docs/current/sql-createrole.html
        log(f"Creating '{lmid}' role ...", console=True)
        password = utils.new_pass(64)

        role_query = self.query.format(f"create role {lmid} with login {'createdb createrole ' if lmid == 'hal' else ''}password '{password}';")
        output = cmd(role_query, catch=True)
        if "already exists" in output:
            log(f"'{lmid}' role already exists!", console=True)
            yes = utils.yes_no("Purge it?")

            if yes: cmd(self.query.format(f"drop database {lmid} if exists; drop role {lmid};"))
            else: return

            cmd(role_query)

        if lmid.startswith("lm"):
            details_path = utils.projects_dir + lmid + "/src/app/db/details.ast"
            details = utils.read(details_path)
            details['pass'] = password
            utils.write(details_path, details)
            return password

        else:
            utils.write(utils.tmp_dir + "db_pass.tmp", password)
            log(f"Password stored in {utils.tmp_dir}db_pass.tmp!", console=True)

    def create_pgdb(self, lmid, host=None):
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
