class Hal:
    lmid = None
    version = None
    settings = None

    app = None
    web = "lm2"
    net = "lm3"
    host = "lm4"
    db = None

    src_dir = utils.get_src_dir()
    app_dir = src_dir + "app/"

    modules = {}
    domains = {}

    lmobjs = {}
    pools = {}

    def start(self):
        # Reset logs
        utils.logs.reset()

        log("Phase 1: Checking integrity ...")

        log("Phase 2: Loading modules ...")
        lib_path = utils.projects_dir + "venv/lib/"
        packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
        sys.path.append(packages_path)

        for module in ('psycopg2', 'yaml'):
            globals()[module] = __import__(module)

        log("Phase 3: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

        utils.logs.level = settings.get("log_level", 1)

        log("Phase 4: Loading database ...")
        self.db = Db(self.lmid)
        self.db.erase()
        self.db.build()

        log("Phase 4.1: Loading modules ...")
        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]   # 1 = utils.dbs
            self.modules[m[1]] = m[0]   # utils.dbs = 1

        log("Phase 4.2: Loading domains ...")
        for d in self.db.execute("select id, name from domains;"):
            self.domains[d[0]] = d[1]
            self.domains[d[1]] = d[0]

        log("Phase 4.3: Loading host environments ...")
        for e in self.db.execute("select id, name from host.envs;"):
            utils.hosts.envs[e[0]] = e[1]
            utils.hosts.envs[e[1]] = e[0]

        log("Phase 4.4: Loading project languages ...")
        for l in self.db.execute("select id, code from project.langs;"):
            utils.projects.langs[l[0]] = l[1]    # 1 = en
            utils.projects.langs[l[1]] = l[0]    # en = 1

        log("Phase 4.5: Loading project themes ...")
        for t in self.db.execute("select id, code from project.themes;"):
            utils.projects.themes[t[0]] = t[1]   # 1 = light
            utils.projects.themes[t[1]] = t[0]   # light = 1

        log("Phase 4.6: Loading web modules ...")
        for m in self.db.execute("select id, name from web.modules;"):
            utils.webs.modules[m[0]] = m[1]    # 1 = static
            utils.webs.modules[m[1]] = m[0]    # static = 1

        log("Phase 4.7: Loading command actions ...")
        for act in hal.db.execute("select id, name, alias from command.acts;"):
            cli.acts[act[0]] = act[1]    # id = name
            cli.acts[act[1]] = act[0]    # name = id
            if act[2]:
                cli.acts[act[2]] = act[0]    # alias = id

        log("Phase 4.8: Loading command objects ...")
        for obj in hal.db.execute("select id, module, name, acts, args, help from command.objs;"):
            cli.objs[obj[0]] = obj[1:]    # id = module, name etc.
            cli.objs[obj[2]] = obj[0]     # name = id

        log("Phase 4.9: Loading command arguments ...")
        for arg in hal.db.execute("select id, act, req, regex, short, long from command.args;"):
            cli.args[arg[0]] = arg[1:]    # id = act, req etc.

        log("Phase 5: Checking services ...")
        ssh.check()
        gitlab.check()

        log("Phase 6: Loading objects ...")
        # Load lm objects
        for lmobj in self.db.execute("select id, lmid, module, alias from lmobjs order by id;"):
            self.lmobjs[lmobj[0]] = lmobj[1:-1]    # 1 = lm1, 10 ('app' module id)
            self.lmobjs[lmobj[1]] = lmobj[0]       # lm1 = 1

            if lmobj[3]:
                self.lmobjs[lmobj[3]] = lmobj[0]   # alias = id

            self.create_pool(lmobj[0])

    def stop(self):
        log("Exiting ...", console=True)
        cli.stop()
        sys.exit()

    def save_settings(self):
        utils.write(self.app_dir + "settings.ast", self.settings)

    def create_pool(self, dbid):
        self.pools[dbid] = getattr(sys.modules[__name__], self.modules[self.lmobjs[dbid][1]])(dbid)
        log(f"Pool {dbid} created.")

    def destroy_pool(self, dbid):
        self.pools.pop(dbid, None)
        log(f"Pool {dbid} destroyed.")

hal = Hal()
