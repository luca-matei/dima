class Hal:
    lmid = None
    version = None
    db = None
    cli = None

    src_dir = utils.get_src_dir()
    app_dir = src_dir + "app/"

    modules = {}
    lmobjs = {}
    pools = {}

    def start(self):
        # Reset logs
        utils.logs.reset()

        log("Phase 1: Loading modules ...")
        lib_path = utils.projects_dir + "venv/lib/"
        packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
        sys.path.append(packages_path)

        for module in ('psycopg2', 'yaml'):
            globals()[module] = __import__(module)

        log("Phase 2: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

        utils.logs.level = settings.get("log_level", 1)

        log("Phase 3: Loading database ...")
        self.db = Db(self.lmid)
        #self.db.erase()
        #self.db.build()
        print(self.db.execute("select 1234;"))

hal = Hal()
