class Hal:
    lmid = None
    version = None

    src_dir = utils.get_src_dir()
    app_dir = src_dir + "app/"

    modules = {}
    lmobjs = {}
    pools = {}

    def __init__(self):
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

    def start(self):
        # Reset logs
        utils.logs.reset()

        log("Phase 1: Loading modules ...")
        lib_path = utils.projects_dir + "venv/lib/"
        packages_path = lib_path + os.listdir(lib_path)[0] + "/site-packages"
        sys.path.append(packages_path)

        for module in ('psycopg2', 'yaml'):
            globals()[module] = __import__(module)


hal = Hal()
