class Db:
    def __init__(self, lmid, dbid=None, host=None):
        self.lmid = lmid
        self.dbid = dbid
        self.host = host
        self.db_dir = utils.projects_dir + lmid + "/src/app/db/"
        self.port_file = utils.projects_dir + "pg_port.txt"

        if self.lmid == dima.app_lmid:
            self.dev_host = dima.host_lmid
            self.host_id = dima.host_dbid
        else:
            self.dev_host = dima.lmobjs.get(dima.db.execute("select dev_host from project.projects where lmobj=%s;", (dbid,))[0][0])[0]
            self.host_id = dima.lmobjs.get(host)

        try:
            self.port = int(utils.read(self.port_file, host=host))
            self.connect()
        except:
            self.check()

    @authorize
    def check(self):
        log(f"Checking '{self.lmid}' database ...", console=True)

        if not utils.read(self.port_file, host=host):
            dima.pools.get(self.host_id).config_postgres()
            self.port = int(utils.read(self.port_file, host=host))
            self.connect()

        if not cmd(utils.dbs.query.format(f"select 1 from pg_database where datname='{lmid}';"), catch=True, host=host):
            dima.pools.get(self.host_id).create_pg_role(self.lmid)
            dima.pools.get(self.host_id).create_pg_db(self.lmid)
            self.connect()

        # Check if database is empty
        if not self.execute("select count(*) from pg_catalog.pg_tables where schemaname not in ('information_schema', 'pg_catalog');")[0][0]:
            self.build()

        log(f"'{self.lmid}' database checked", console=True)

    @authorize
    def connect(self):
        try:
            if self.host and self.host != dima.host_lmid:
                ip = dima.pools.get(dima.lmobjs.get(self.host)).ip
            else:
                ip = "127.0.0.1"

            if utils.isfile(self.db_dir + "db_pass.txt", host=self.host):
                # Password file exists
                password = utils.read(self.db_dir + "db_pass.txt", host=self.host)
            else:
                # Password file has been removed
                if utils.confirm(f"Couldn't find password for database '{self.lmid}' on host '{self.host}'! Purge database? Manual intervention is required otherwise!"):
                    dima.pools.get(self.host_id).create_pg_role(self.lmid)
                    dima.pools.get(self.host_id).create_pg_db(self.lmid)

                    password = utils.read(self.db_dir + "db_pass.txt", host=self.host)
                else:
                    log(f"Required manual intervention for database '{self.lmid}' on '{self.host}' to change password!", level=5, console=True)

            self.conn = psycopg2.connect(f"dbname={self.lmid} user={self.lmid} host={ip} password={password} port={self.port}")

        except Exception as e:
            log(e, level=4)
            log(f"Cannot connect to '{self.lmid}' database!", level=4, console=True)
            task.abort()

        log(self.lmid + " database connected")

    @authorize
    def rebuild(self):
        self.erase()
        self.build()

    @authorize
    def format_table(self, table):
        self.execute(f"truncate {table};")

    @authorize
    def erase(self):
        log(f"Erasing '{self.lmid}' database ...", level=3, console=True)

        # Drop all user created schemas
        schemas = [x[0] for x in self.execute("select s.nspname as table_schema, s.oid as schema_id, u.usename as owner from pg_catalog.pg_namespace s join pg_catalog.pg_user u on u.usesysid = s.nspowner where nspname not in ('information_schema', 'pg_catalog', 'public') and nspname not like 'pg_toast%%' and nspname not like 'pg_temp_%%' order by table_schema;")]
        for schema in schemas:
            self.execute(f"drop schema if exists {schema} cascade;")

        # Drop all remaining user created tables
        tables = [x[0] for x in self.execute("select table_name from information_schema.tables where table_schema='public';")]
        for table in tables:
            self.execute(f"drop table if exists {table} cascade;")

        log(f"'{self.lmid}' database erased", console=True)

    @authorize
    def build(self):
        log(f"Building '{self.lmid}' database on '{self.dev_host}' ...", console=True)
        struct = utils.read(self.db_dir + "struct.ast", host=self.dev_host)
        default_file = self.db_dir + "default.ast"

        for group in struct:
            # Check if the group is a schema
            # group[0] is the schema name / public table name
            # group[1] is the list of tables / of rows
            # group[1][0] is the first table / first row
            if isinstance(group[1][0], tuple):
                self.execute(f"create schema {group[0]};")
                for table in group[1]:
                    self.execute(f"create table {group[0]}.{table[0]} ({','.join(table[1])});")

            # The group is a table
            else:
                self.execute(f"create table {group[0]} ({','.join(group[1])});")

        self.load(default_file)
        log(f"'{self.lmid}' database built on '{self.dev_host}'", console=True)

    @authorize
    def load(self, file):
        """
        INSERT into scratch (name, rep_id, term_id)
        SELECT 'aaa'
                , r.id
                , t.id
        FROM reps r , terms t -- essentially a cross join
        WHERE r.rep = 'Dracula'
          AND t.terms = 'prepaid';

        Special first row for translating columns from a table
        """

        log(f"Loading '{file}' into '{self.lmid}' ...", console=True)

        db_data = utils.read(file, host=self.dev_host)
        for schema in db_data:
            for table in schema[1]:
                struct_row = ', '.join(table[1][0])    # Db structure row
                nmsps = []
                nmsp_tables = []
                nmsp_table_i = 0    # Letter for the namespace table; nets a, guests b etc.
                has_nmsps = False

                for nmsp in table[1][1]:    # Column namespaces row
                    if nmsp:
                        has_nmsps = True
                        nmsp_list = nmsp.split(':')    # translated column, column to translate, table

                        # Lists of namespaces will be treated differently later
                        if not nmsp_list[0].endswith('[]'):
                            nmsp_tables.append(nmsp_list[2] + ' ' + utils.abc[nmsp_table_i])
                            nmsp_list[2] = utils.abc[nmsp_table_i]    # Replace table name with letter
                            nmsp_table_i += 1    # Move forward in the alphabet
                        else:
                            nmsp_list[0] = nmsp_list[0][:-2]    # Remove '[]'

                        nmsps.append(nmsp_list)
                    else:
                        nmsps.append('')

                # To do: validate data
                if has_nmsps:
                    for row in table[1][2:]:    # Data rows
                        tmp_nmsp_tables = nmsp_tables
                        new_row = []
                        wheres = []    # where clause in query

                        for i, col in enumerate(row):
                            if nmsps[i]:
                                # Check if it's a list of namespaces
                                if isinstance(col, tuple):
                                    if col:
                                        query = f"select {nmsps[i][0]} from {nmsps[i][2]} where {nmsps[i][1]} in %s;"
                                        params = col,
                                        values = [x[0] for x in self.execute(query, params)]
                                        sql_list = []

                                        for value in values:
                                            if isinstance(value, str):
                                                if value:
                                                    sql_list.append(f"'{value}'")
                                                else:
                                                    sql_list.append("null")
                                            else:
                                                sql_list.append(str(value))

                                        new_row.append("'{" + ', '.join(sql_list) + "}'")
                                    else:
                                        new_row.append("'{}'")
                                else:
                                    if col:
                                        new_row.append(nmsps[i][2] + '.' + nmsps[i][0])                 # Table letter . Translated column
                                        wheres.append(nmsps[i][2] + '.' + nmsps[i][1] + f"='{col}'")    # Table letter . Column to translate
                                    else:
                                        new_row.append("null")
                                        tmp_nmsp_tables = [x for x in tmp_nmsp_tables if x[-1] != nmsps[i][2]]

                            # Column doesn't have a namespace
                            else:
                                if isinstance(col, str):
                                    if col:
                                        new_row.append(f"'{col}'")
                                    else:
                                        new_row.append("null")
                                else:
                                    new_row.append(str(col))

                        new_row = ', '.join(new_row)
                        wheres = ' and '.join(wheres)

                        self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) select {new_row} from {', '.join(tmp_nmsp_tables)} where {wheres};")
                else:
                    rows = []
                    ss = []
                    for row in table[1][2:]:
                        rows.extend([None if not value and isinstance(value, str) else value for value in row])
                        ss.append(f"({', '.join(['%s' for x in row])})")
                    ss = ', '.join(ss)

                    self.execute(f"insert into {schema[0]}.{table[0]} ({struct_row}) values {ss};", rows)

        log(f"Loaded '{file}'", console=True)

    @authorize
    def export(self, file_path=""):
        if not file_path: file_path = f"/home/dima/tmp/{self.lmid}.db.ast"
        log(f"Exported {self.lmid} database to {file_path}", console=True)

    def log(self, *args, **kwargs):
        logs._log(self.call_info, *args, **kwargs)

    @authorize
    def execute(self, query, params=()):
        a = inspect.currentframe()
        self.call_info = list(inspect.getframeinfo(a.f_back)[:3])

        data = ()
        for tries in range(2):
            try:
                cursor = self.conn.cursor()
                break
            except:
                cursor = None

        if cursor == None:
            self.log("No database cursor!", level=5, console=True)
        else:
            self.log(f"Query: {query}")
            if params: self.log(f"Params: {params}")

            try:
                cursor.execute(query, params)
                if query.startswith("select") or "returning" in query:
                    data = cursor.fetchall()
                    self.log(f"Data: {data}")

            except (Exception, psycopg2.Error) as e:
                # Hitting 'restart postgres will terminate active connections'
                if "server closed the connection" in str(e):
                    self.connect()
                    return self.execute(query, params)

                self.log(f"Query error: {e}", level=4)
                self.log(f"Database error!", level=5, console=True)

            self.conn.commit()
            cursor.close()
        return data

    @authorize
    def disconnect(self):
        self.conn.close()
        log(self.lmid + " database disconnected")
