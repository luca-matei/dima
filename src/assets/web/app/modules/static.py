class lmStatic:
    def fetch(self, page_id):
        query = "select html from pages where id=%s;"
        params = page_id,
        return lm.db.execute(query, params)[0][0]

lm.static = lmStatic()
