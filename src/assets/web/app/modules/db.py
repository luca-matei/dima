class lmDb:
    def connect(self):
        # To do: get passwords securely
        details = util.read(lm.app_dir + "db.ast")
        host = details['host']
        port = details['port']
        password = details['password']

        self.conn = psycopg2.connect(
            dbname = lm.lmid,
            user = lm.lmid,
            host = host,
            port = port,
            password = password,
            )

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
                log(f"Query error: {e}", level=4)
                log(f"Database error!", level=5, console=True)

            self.conn.commit()
            cursor.close()
        return data

    def disconnect(self):
        self.conn.close()
        log(self.lmid + " database disconnected.")

lm.db = lmDb()
