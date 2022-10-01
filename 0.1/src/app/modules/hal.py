class Hal:
    lmid = None
    version = None

    modules = {}
    lmobjs = {}
    pools = {}

    def __init__(self):
        # Load core settings
        settings = utils.read(utils.src_dir + "app/settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

    def start(self):
        # Reset logs
        utils.logs.reset()

hal = Hal()
