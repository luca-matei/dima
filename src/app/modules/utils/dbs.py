class DbUtils:
    query = """sudo -u hal psql -tAc \"{}\""""

    def create_role(self, lmid, host=""):
        password = utils.new_pass(64)

        # Check if role's to be created on another machine
        if host: return 0
        # Create the role if it doesn't already exist
        else:
            output = cmd(self.query.format(f"create role {lmid} with login password '{password}';"), catch=True)

        if "already exists" in output:
            log(f"Role {lmid + ' on host ' + host if host else lmid} already exists! Drop the databases that use it to recreate it.", level=4, console=True)
        else:
            return password

        return 0

utils.dbs = DbUtils()
