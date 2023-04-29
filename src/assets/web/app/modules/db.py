class lmDb:
    def __init__(self):
        self.db_dir = lm.app_dir + "db/"

    def connect(self):
        host = "127.0.0.1"
        port = int(utils.read(utils.projects_dir + "pg_port.txt"))
        password = utils.read(self.db_dir + "db_pass.txt")

        self.conn = psycopg2.connect(f"dbname={lm.lmid} user={lm.lmid} host={host} password={password} port={port}")

        log(lm.lmid + " database connected.")

    def execute(self, query, params=()):
        data = ()
        for tries in range(2):
            try:
                cursor = self.conn.cursor()
                break
            except:
                cursor = None

        if cursor == None:
            log("No database cursor!", level=5, console=True)
        else:
            log(f"Query: {query}")
            if params: log(f"Params: {params}")

            try:
                cursor.execute(query, params)
                if query.startswith("select") or "returning" in query:
                    data = cursor.fetchall()
                    log(f"Data: {data}")

            except (Exception, psycopg2.Error) as e:
                if "server closed the connection" in str(e):
                    self.connect()
                    return self.execute(query, params)

                log(f"Query error: {e}", level=4)
                log(f"Database error!", level=5, console=True)

            self.conn.commit()
            cursor.close()
        return data

    def disconnect(self):
        self.conn.close()
        log(self.lmid + " database disconnected.")

lm.db = lmDb()
