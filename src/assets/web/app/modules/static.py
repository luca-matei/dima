class lmStatic:
    fractions = {}

    def fetch_fraction(self, fraction):
        query = "select html from fractions where id=%s;"
        params = self.fractions[lm.request.lang_id][fraction],

        return lm.db.execute(query, params)[0][0]

    def fetch_page(self, page_id):
        query = "select html from pages where id=%s;"
        params = page_id,
        return lm.db.execute(query, params)[0][0]

lm.static = lmStatic()
