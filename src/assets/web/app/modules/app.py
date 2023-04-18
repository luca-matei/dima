class lmApp:
    lmid = None
    domain = None
    db = None

    langs = {}
    modules = {}

    sections = {}
    pages = {}
    first_pages = {}

    themes = None
    default_theme = None
    default_lang = None

    app_dir = utils.src_dir + "app/"

    def start(self):
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        logs.level = settings.get("log_level")
        logs.reset()

        log("Loading settings ...")
        for s in ("lmid", "domain", "default_lang", "default_theme"):
            setattr(self, s, settings.get(s))

        self.db.connect()

        for m in self.db.execute("select id, name from methods;"):
            lm.http.methods[m[0]] = m[1]    # 1 = get
            lm.http.methods[m[1]] = m[0]    # get = 1

        for l in self.db.execute("select id, code from langs;"):
            self.langs[l[0]] = l[1]    # 1 = en
            self.langs[l[1]] = l[0]    # en = 1

        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]    # 1 = static
            self.modules[m[1]] = m[0]    # static = 1


        for s in self.db.execute("select id, name, parent from sections;"):
            parent = s[2]
            if not self.sections.get(parent):
                self.sections[parent] = {}

            self.sections[parent][s[0]] = s[1]    # id = name
            self.sections[parent][s[1]] = s[0]    # name = id

        # Home
        self.sections[0][''] = self.sections[0]["home"]

        for p in self.db.execute("select section, name, lang, method, id, module, first from pages;"):
            parent = p[0]    # id
            name = p[1]
            lang = p[2]    # id
            method = p[3]    # id

            if not self.pages.get(parent):
                self.pages[parent] = {}

            if not self.pages[parent].get(name):
                self.pages[parent][name] = {}

            if not self.pages[parent][name].get(lang):
                self.pages[parent][name][lang] = {}

            if not self.pages[parent][name][lang].get(method):
                self.pages[parent][name][lang][method] = p[4:-1]

            if p[6]:
                self.first_pages[parent] = name    # about -> myself

        log(self.sections)
        log(self.pages)
        log(self.first_pages)


        for l in [l_id for l_id in utils.get_keys(self.langs) if isinstance(l_id, int)]:
            lm.static.fractions[l] = {}

        for f in self.db.execute("select lang, id, name from fractions;"):
            lm.static.fractions[f[0]][f[1]] = f[2]
            lm.static.fractions[f[0]][f[2]] = f[1]

lm = lmApp()
