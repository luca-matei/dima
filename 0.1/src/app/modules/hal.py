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

hal = Hal()
