class SSH:
    keygen = 'ssh-keygen -b 4096 -t ed25519 -a 100 -f {} -q -N ""'

    def create_ssh_key(self, name:'str', host:'str'=dima.host_lmid):
        log(f"Creating SSH Key '{name}' ...", console=True)
        privkey = utils.ssh_dir + name
        if utils.isfile(privkey, host=host):
            if utils.confirm("SSH key already exists! Overwrite it?"):
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(self.keygen.format(privkey), host=host)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)
            log(f"Created SSH Key '{name}'", console=True)
        else:
            log(f"Couldn't generate SSH Key '{name}'!", level=4, console=True)

ssh = SSH()
