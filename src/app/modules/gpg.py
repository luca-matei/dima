class GPG:
    def create_gpg_key(self, email):
        log(f"Generating GPG key for '{email}'. This may take a while ...", console=True)

        key_config = utils.format_tpl("gpg-key.tpl", {
            "user": email.split('@')[0],
            "email": email
            })
        utils.write(utils.tmp_dir + "gpg", key_config)

        cmd(f"gpg2 --batch --gen-key {utils.tmp_dir}gpg")

        return self.get_privkey_id(email)

    def get_privkey_id(self, email):
        privkey_id = cmd(f"gpg2 --list-secret-keys --keyid-format LONG {email}", catch=True)
        if not "No secret key" in privkey_id:
            return re.findall(r'\bsec   rsa4096/\w+', privkey_id)[0].split('/')[1]
        else:
            log(f"Couldn't find GPG key for '{email}'!", level=4, console=True)
            yes = utils.yes_no("Create one?")
            if yes:
                return self.create_gpg_key(email)
            return 0

    def delete_gpg_key(self, host):
        cmd(f"gpg2 --batch --delete-secret-keys {email}")
        cmd(f"gpg2 --batch --delete-keys {email}")

gpg = GPG()
