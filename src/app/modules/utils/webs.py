class WebUtils:
    methods = "get", "put", "post", "delete"
    modules = {}

    def create_web(self, domain:'str', name:'str'="", description:'str'="", alias:'str'="", modules:'list'=(), langs:'list'=(), themes:'list'=(), default_lang:'str'="", default_theme:'str'="", has_animations=False):
        self.__doc__ = Host.create_web.__doc__
        # To do: choose a host and invoke create_web()
        host_dbid = hal.lmobjs["lm8"]

        hal.pools.get(host_dbid).create_host(env, alias, mem, cpus, disk)

utils.webs = WebUtils()
