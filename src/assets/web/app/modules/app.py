class lmApp:
    lmid = None
    domain = None
    themes = None
    langs = {}
    modules = {}
    sections = {}
    pages = {}
    first_pages = {}
    app_dir = utils.src_dir + "app/"

    db = None

    def start(self):
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        logs.level = settings.get("log_level")
        logs.reset()

        log("Loading settings ...")
        for s in ("lmid", "domain"):
            setattr(self, s, settings.get(s))

        self.db.connect()

        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]    # 1 = static
            self.modules[m[1]] = m[0]    # static = 1

        for s in self.db.execute("select id, name, parent from sections;"):
            for i in (0, 2):
                if s[i] not in utils.get_keys(self.sections):
                    self.sections[s[i]] = {}
                    self.pages[s[i]] = {}
                    self.first_pages[s[i]] = {}

            self.sections[s[2]].update({s[1]: s[0]})

        for l in self.db.execute("select id, code from langs;"):
            self.langs[l[0]] = l[1]    # 1 = en
            self.langs[l[1]] = l[0]    # en = 1

            for s in utils.get_keys(self.sections):
                self.pages[s][l[0]] = {}
                self.first_pages[s][l[0]] = {}

        for m in self.db.execute("select id, name from methods;"):
            lm.http.methods[m[0]] = m[1]    # 1 = get
            lm.http.methods[m[1]] = m[0]    # get = 1

            for s in utils.get_keys(self.sections):
                for l in [l_id for l_id in utils.get_keys(self.langs) if isinstance(l_id, int)]:
                    self.pages[s][l][m[0]] = {}
                    self.first_pages[s][l][m[0]] = {}

        for p in self.db.execute("select id, name, module, section, method, lang, first from pages;"):
            page_id = p[0]
            section_id = p[3]
            method_id = p[4]
            lang_id = p[5]

            self.pages[section_id][lang_id][method_id][page_id] = p[1], p[2],
            self.pages[section_id][lang_id][method_id][p[1]] = page_id

            if p[6]:
                self.first_pages[section_id][lang_id][method_id] = page_id

lm = lmApp()
