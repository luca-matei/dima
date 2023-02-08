class SSH:
    keygen = 'ssh-keygen -b 4096 -t ed25519 -a 100 -f {} -q -N ""'

    def create_ssh_key(self, name:'str', host:'str'=hal.host_lmid):
        privkey = utils.ssh_dir + name
        if utils.isfile(privkey, host=host):
            log(f"SSH key already exists!", level=3, console=True)
            yes = utils.yes_no("Overwrite it?")
            if yes:
                cmd(f"mv {privkey} {privkey}.old", host=host)
                cmd(f"mv {privkey}.pub {privkey}.pub.old", host=host)
            else:
                return

        cmd(self.keygen.format(privkey), host=host)

        if utils.isfile(privkey, host=host):
            cmd("chmod 600 " + privkey, host=host)
            cmd("chmod 600 " + privkey + ".pub", host=host)
            log("SSH key created!", console=True)
        else:
            log(f"Couldn't generate SSH key to access {name}!", level=4, console=True)

ssh = SSH()
