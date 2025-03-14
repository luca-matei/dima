class Dima:
    lmid = None
    version = None
    settings = None

    app_dbid = None
    web_dbid = None
    net_dbid = None
    host_dbid = None
    db = None

    app_lmid = "lm1"
    web_lmid = "lm2"
    net_lmid = "lm3"
    host_lmid = "lm4"

    domain = None

    modules = {}
    lmobjs = {}
    pools = {}

    def status(self):
        print(utils.new_pass(64))

    def start(self):
        self.app_dir = utils.src_dir + "app/"
        self.tpls_dir = utils.src_dir + "assets/tpls/"

        # Reset logs
        logs.reset()

        log("Phase 1: Checking integrity ...")

        log("Phase 2: Loading modules ...")
        utils.tpl_header = utils.read(self.tpls_dir + "header.tpl")

        log("Phase 3: Loading settings ...")
        # Load core settings
        settings = utils.read(self.app_dir + "settings.ast")
        self.settings = settings

        for attr in ("lmid", "version", "domain"):
            setattr(self, attr, settings.get(attr))

        logs.level = settings.get("log_level", 1)
        gitlab.domain = settings.get("gitlab_domain")
        gitlab.user = settings.get("gitlab_user")
        utils.hosts.domain = settings.get("hosts_domain")

        log("Phase 4: Loading database ...")
        self.db = Db(self.lmid)
        self.db.rebuild()

        self.load_database()

        log("Phase 5: Checking services ...")
        #self.check()
        #ssh.check()
        gitlab.get_token()

        log("Phase 6.1: Creating object pools ...")
        for kind in (self.modules["Net"], self.modules["Host"], self.modules["DNS"], self.modules["Soft"], self.modules["App"], self.modules["Web"]):
            for dbid in utils.get_keys(self.lmobjs):
                if isinstance(dbid, int) and self.lmobjs[dbid][1] == kind:
                    self.create_pool(dbid)

        """
        log("Phase 7: Checking objects ...")
        for dbid in utils.get_keys(self.lmobjs):
            self.pools.get(dbid).check()
        """


    def load_database(self):
        log("Phase 4.1: Loading modules ...")
        for m in self.db.execute("select id, name from modules;"):
            self.modules[m[0]] = m[1]   # 1 = utils.dbs
            self.modules[m[1]] = m[0]   # utils.dbs = 1

        log("Phase 4.2: Loading zones ...")
        cols = "pub_dns", "priv_dns", "pub_mail", "priv_mail",
        for z in self.db.execute(f"select name, {', '.join(cols)} from net.zones;"):
            utils.nets.zones[z[0]] = dict(zip(cols, z[1:]))

        log("Phase 4.3.1: Loading host environments ...")
        for e in self.db.execute("select id, name from host.envs;"):
            utils.hosts.envs[e[0]] = e[1]
            utils.hosts.envs[e[1]] = e[0]

        log("Phase 4.3.2 Loading host services ...")
        for s in self.db.execute("select id, name from host.services;"):
            utils.hosts.services[s[0]] = s[1]
            utils.hosts.services[s[1]] = s[0]

        log("Phase 4.4.1: Loading project languages ...")
        for l in self.db.execute("select id, code from project.langs;"):
            utils.projects.langs[l[0]] = l[1]    # 1 = en
            utils.projects.langs[l[1]] = l[0]    # en = 1

        log("Phase 4.4.2: Loading project themes ...")
        for t in self.db.execute("select id, code from project.themes;"):
            utils.projects.themes[t[0]] = t[1]   # 1 = light
            utils.projects.themes[t[1]] = t[0]   # light = 1

        log("Phase 4.4.3: Loading project options ...")
        for o in self.db.execute("select id, name from project.options;"):
            utils.projects.options[o[0]] = o[1]   # 1 = animations
            utils.projects.options[o[1]] = o[0]   # animations = 1

        log("Phase 4.6: Loading web modules ...")
        for m in self.db.execute("select id, name from web.modules;"):
            utils.webs.modules[m[0]] = m[1]    # 1 = static
            utils.webs.modules[m[1]] = m[0]    # static = 1

        log("Phase 4.7: Loading command actions ...")
        for act in dima.db.execute("select id, name, alias from command.acts;"):
            cli.acts[act[0]] = act[1]    # id = name
            cli.acts[act[1]] = act[0]    # name = id
            if act[2]:
                cli.acts[act[2]] = act[0]    # alias = id

        log("Phase 4.8: Loading command objects ...")
        module_ids = []
        for obj in dima.db.execute("select id, module, name, acts from command.objs;"):
            module_id = obj[1]
            if module_id not in module_ids:
                cli.objs[module_id] = {}
                module_ids.append(module_id)

            if obj[2] == None: name = ""
            else: name = obj[2]
            cli.objs[module_id][obj[0]] = obj[2:]    # id = name, acts, args
            cli.objs[module_id][name] = obj[0]     # name = id

        log("Phase 4.9: Loading objects data ...")
        # Load lm objects
        for lmobj in self.db.execute("select id, lmid, module, alias from lmobjs order by id;"):
            self.lmobjs[lmobj[0]] = lmobj[1:]      # 1 = lm1, 10 ('app' module id), astatin
            self.lmobjs[lmobj[1]] = lmobj[0]       # lm1 = 1

            if lmobj[3]:
                self.lmobjs[lmobj[3]] = lmobj[0]   # alias = id

            if lmobj[1] == "lm1": self.app_dbid = lmobj[0]
            elif lmobj[1] == "lm2": self.web_dbid = lmobj[0]
            elif lmobj[1] == "lm3": self.net_dbid = lmobj[0]
            elif lmobj[1] == "lm4": self.host_dbid = lmobj[0]

    def stop(self):
        log("Exiting ...", console=True)
        cli.stop()
        sys.exit()

    def save_settings(self):
        utils.write(self.app_dir + "settings.ast", self.settings)

    def create_pool(self, dbid):
        self.pools[dbid] = getattr(sys.modules[__name__], self.modules[self.lmobjs[dbid][1]])(dbid)
        log(f"Pool {dbid} created")

    def destroy_pool(self, dbid):
        self.pools.pop(dbid, None)
        log(f"Pool {dbid} destroyed")

    def insert_lmobj(self, lmid, module, alias):
        log(f"Inserting {lmid} of type {module} ...")
        module_id = dima.modules[module]

        query = f"insert into lmobjs (lmid, module, alias) values (%s, %s, %s) returning id;"
        params = lmid, module_id, alias,
        dbid = dima.db.execute(query, params)[0][0]

        dima.lmobjs[dbid] = list(params)
        dima.lmobjs[lmid] = dbid
        if alias: dima.lmobjs[alias] = dbid

        return dbid

    def next_lmid(self):
        taken = [int(lmid[0][2:]) for lmid in dima.db.execute("select lmid from lmobjs;")]

        for i in range(1, 1000):
            if i not in taken:
                return f"lm{i}"

    def check_alias(self, alias):
        forbidden = "", "q", "exit"

        if alias in forbidden or alias.startswith("lm") or cli.acts.get(alias):
            log("Can't assign this alias!", level=4, console=True)
            return 0

        elif self.lmobjs.get(alias):
            log(f"Alias already in use by {self.lmobjs[self.lmobjs[alias]][0]}!", level=4, console=True)
            return 0

        else:
            return 1

    def generate_password(self, length:'int'=64):
        print(utils.new_pass(length))

    def check(self):
        """
        iface = netifaces.interfaces()[1]
        addrs = netifaces.ifaddresses(iface)
        net = addrs[netifaces.AF_INET][0]
        ip, netmask, broadcast = net['addr'], net['netmask'], net['broadcast']
        mac = addrs[netifaces.AF_LINK][0]['addr']
        network = ipaddress.ip_network(ip + '/' + netmask, strict=False)
        gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
        """

        reload = False
        # To do: validate registration details

        for d in (self.domain, 'home.' + self.domain):
            domain_id = self.db.execute("select id from net.domains where name=%s;", (d,))[0][0]

            if not domain_id:
                domain_id = self.db.execute("insert into net.domains (name) values (%s) returning id;", (d,))[0][0]
                reload = True

        if not self.net_dbid:
            log("Main network not registered!", level=3, console=True)
            self.net_dbid = self.insert_lmobj(self.net_lmid, "Net", None)

            query = "insert into net.nets (lmobj, domain, netmask, gateway, lease_start, lease_end) values (%s, %s, %s, %s, %s, %s);"
            params = self.net_dbid, domain_id, netmask, gateway, str(network[4]), str(network[-2]),

            self.db.execute(query, params)
            reload = True

        if not self.host_dbid:
            # https://pypi.org/project/netifaces/
            log("Main host not registered!", level=3, console=True)
            self.host_dbid = self.insert_lmobj(self.host_lmid, "Host", utils.hostname)

            query = "insert into host.hosts (lmobj, mac, net, ip, client, env, ssh_port, pg_port, pm) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
            params = self.host_dbid, mac, self.net_dbid, ip, None, utils.hosts.envs["dev"], None, None, None,

            self.db.execute(query, params)
            reload = True

        if not self.app_dbid:
            self.app_dbid = self.insert_lmobj(self.app_lmid, "App", "dima")

            # Register project
            query = "insert into project.projects (lmobj, dev_host, dev_version, prod_host, prod_version, name, description) values (%s, %s, %s, %s, %s, %s, %s);"
            params = self.app_dbid, self.host_dbid, self.version, None, None, "dima", None,
            self.db.execute(query, params)

            # Register app
            query = "insert into project.apps (lmobj, port) values (%s, %s);"
            params = self.app_dbid, None,
            self.db.execute(query, params)

            reload = True

        if not self.web_dbid:
            reload = True

        if reload:
            self.load_database()

dima = Dima()
