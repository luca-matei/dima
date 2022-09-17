class App:
    lmid = None
    version = None
    src_dir = None

    def __init__(self):
        # Load core settings
        settings = utils.read("./settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

        self.src_dir = utils.projects_dir + self.lmid + '/' + self.version + '/src/'

    def start(self):
        # Reset logs
        utils.logs.reset()

    def stop(self):
        log("Exiting ...", console=True)
        sys.exit()

app = App()
