class App:
    lmid = None
    version = None

    def __init__(self):
        # Load core settings
        print(utils.src_dir)
        settings = utils.read(utils.src_dir + "app/settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

    def start(self):
        # Reset logs
        utils.logs.reset()

    def stop(self):
        log("Exiting ...", console=True)
        sys.exit()

app = App()
