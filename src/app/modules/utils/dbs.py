class DbUtils:
    query = """sudo -u dima psql -tAc \"{}\""""
    port_file = utils.projects_dir + "pg_port.txt"

utils.dbs = DbUtils()
