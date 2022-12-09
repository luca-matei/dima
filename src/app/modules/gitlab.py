class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

    def request(self, method="get", endpoint="", data={}):
        method = method.lower()
        if method not in ("get", "post", "delete"):
            log(f"Invalid method '{method}'!", level=4)
            return 0

        headers = {'private-token': self.get_token()}
        url = f"https://{self.domain}/api/v4{endpoint}"

        response = getattr(requests, method)(
            url,
            headers = headers,
            json = data
            )

        return response.json()

    def clone(self, lmid):
        log(f"Cloning {lmid} Gitlab repository ...")
        cmd(f"git clone git@{self.domain}:{self.user}/{lmid}.git {utils.projects_dir}{lmid}/")

    def add_ssh_key(self, host):
        if hal.ssh.create_sshkey(host + "-gitlab"):
            data = {
                'title': host,
                'key': util.read(hal.ssh.keys_dir + host + "-gitlab.pub")
                }

            self.request(
                    method = "post",
                    endpoint = "/user/keys",
                    data = data
                    )

    def delete_ssh_key(self, host):
        hal.ssh.delete_sshkey(host + '-gitlab')
        self.request(
            method = "delete",
            endpoint = "/user/keys/" + self.get_ssh_keys(host).get('id')
            )

    def get_ssh_keys(self, host=None):
        keys = self.request(endpoint = "/user/keys")

        if host:
            key = None
            for k in keys:
                if k.get("title") == host:
                    key = k
                    break
            return key

        return keys

    def get_gpg_keys(self):
        keys = self.request(endpoint = "/user/gpg_keys")
        return keys

    def add_email(self, email):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': email}
            )

    def add_gpg_key(self, host):
        email = f"{host}@{self.domain}"
        privkey_id = hal.gpg.create_gpgkey(email)

        if privkey_id:
            pubkey = cmd("gpg2 --armor --export " + privkey_id, catch=True)

            self.add_email(email)
            self.request (
                method = "post",
                endpoint = "/user/gpg_keys",
                data =  {'key': pubkey}
                )

            cmd("git config --global user.signingkey " + privkey_id)

    def get_projects(self, lmid=None):
        projects = self.request(endpoint = "/projects")

        if lmid:
            project = None
            for p in projects:
                if p.get("path") == lmid:
                    project = p
                    break
            return project

        return projects

    def create_project(self, data):
        self.request(
            method = "post",
            endpoint = "/projects",
            data = data
        )

    def get_token(self):
        token_file = hal.app_dir + 'token.txt'

        # To do: Save it securely
        if not util.isfile(token_file):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token.")

            token = getpass.getpass("Token: ")
            util.write(token_file, token)

            return token
        else:
            return util.read(token_file)

    def check(self):
        if not util.isfile(f"/home/{hal.user}/.gitconfig"):
            self.config_git()

        if not self.get_ssh_keys(hal.host_lmid):
            self.add_ssh_key(hal.host_lmid)

        if not self.get_gpg_keys():
            self.add_gpg_key(hal.host_lmid)

gitlab = Gitlab()
