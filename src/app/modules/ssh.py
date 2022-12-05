class SSH:
    keys_dir = utils.ssh_dir + 'keys/'

    def config_ssh(self, gitlab=False):
        log(f"Configuring SSH for {hal.host_lmid} ...")

        cmd(f"cp {hal.tpl_dir}ssh/client.tpl /home/{hal.user}/.ssh/config")

        config = ""
        if gitlab:
            gitlab_config = util.read(hal.tpl_dir + "ssh/gitlab.tpl")
            for privkey in cmd(f"ls {self.keys_dir}*-gitlab", catch=True).split('\n'):
                config += gitlab_config.replace("%PRIVKEY", privkey)

            util.write(hal.ssh_dir + "gitlab.conf", config)

        else:
            host_config = util.read(hal.tpl_dir + "ssh/host.tpl")

            query = "select a.lmid, b.ip, b.ssh_port from lmobjs a, guests b where a.id = b.lmobj and a.id != %s;"
            params = hal.host_dbid,
            guests = hal.db.execute(query, params)

            for guest in guests:
                config += host_config \
                    .replace("%LMID", guest[0]) \
                    .replace("%IP", guest[1]) \
                    .replace("%PORT", guest[2]) \
                    .replace("%USER", "hal") \
                    .replace("%PUBKEY", self.keys_dir + guest[0])

            util.write(hal.ssh_dir + "hosts.conf", config)

    def create_sshkey(self, host):
        log(f"Generating SSH key to access host '{host}'. This may take a while ...", console=True)
        cmd(f'ssh-keygen -b 4096 -t ed25519 -a 100 -f {self.keys_dir + host} -q -N ""')

        if util.isfile(self.keys_dir + host):
            cmd("chmod 600 " + self.keys_dir + host)
            cmd("chmod 600 " + self.keys_dir + host + ".pub")
            self.config_ssh(gitlab = host.endswith("gitlab"))
            return 1
        else:
            log(f"Couldn't generate SSH key to access host '{host}'!", level=4)
            return 0

    def delete_sshkey(self, host):
        log(f"Removing SSH key for host '{host}' ...")

        privkey = util.keys_dir + host
        cmd(f"rm {privkey} {privkey}.pub")

        self.config_ssh(gitlab = host.endswith("gitlab"))

    def check(self):
        if not util.isfile(f"/home/{hal.user}/.ssh/config"):
            self.config_ssh()

ssh = SSH()
