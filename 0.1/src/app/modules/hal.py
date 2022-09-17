class App:
    lmid = None
    version = None

    def start(self):
        # Load core settings
        settings = utils.read(utils.src_dir + "app/settings.ast")
        for attr in ("lmid", "version"):
            setattr(self, attr, settings.get(attr))

        # Reset logs
        utils.logs.reset()

    def stop(self):
        log("Exiting ...", console=True)
        sys.exit()

app = App()
