class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

    def __init__(self, host_dbid, host_lmid):
        self.host_dbid = host_dbid
        self.host_lmid = host_lmid
        self.email = f"{host_lmid}@{self.domain}"

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
        cmd(f"git clone git@{self.domain}:{self.user}/{lmid}.git {utils.projects_dir}{lmid}/", host=self.host_lmid)

    def add_ssh_key(self):
        if hal.pools.get(self.host_dbid).create_ssh_key(gitlab=True):
            data = {
                'title': self.host_lmid,
                'key': utils.read(utils.ssh_dir + self.host_lmid + "-gitlab.pub", host=self.host_lmid)
                }

            self.request(
                    method = "post",
                    endpoint = "/user/keys",
                    data = data
                    )

    def delete_ssh_key(self):
        hal.pools.get(self.host_dbid).delete_ssh_key(gitlab=True)
        self.request(
            method = "delete",
            endpoint = "/user/keys/" + self.get_ssh_keys(self.host_lmid).get('id')
            )

    def get_ssh_key(self):
        key = None
        for k in self.request(endpoint = "/user/keys"):
            if k.get("title") == self.host_lmid:
                key = k
                break
        return key

    def get_gpg_keys(self):
        keys = self.request(endpoint = "/user/gpg_keys")
        return keys

    def add_email(self):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': self.email}
            )

    def add_gpg_key(self):
        privkey_id = gpg.create_gpg_key(self.email)

        if privkey_id:
            pubkey = cmd("gpg2 --armor --export " + privkey_id, catch=True)

            self.add_email()
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

    def config_git(self):
        log(f"Configuring Git for {self.host_lmid} ...", console=True)
        config = utils.format_tpl("gitconfig.tpl", {
            "user": self.host_lmid,
            "email": self.email,
            "gpg_key": gpg.get_privkey_id(self.host_lmid)
            })
        utils.write(f"/home/hal/.gitconfig", config, host=self.host_lmid)

    def get_token(self):
        token_file = utils.projects_dir + 'gitlab_token.txt'

        if not utils.isfile(token_file, host=self.host_lmid):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token.")

            token = getpass.getpass("Token: ")
            utils.write(token_file, token, host=self.host_lmid)
            cmd("chmod 600 " + token_file, host=self.host_lmid)

            return token
        else:
            return utils.read(token_file, host=self.host_lmid)

    def check(self):
        if not utils.isfile("/home/hal/.gitconfig"):
            self.config_git()

        if not gitlab.get_ssh_keys(self.lmid):
            gitlab.add_ssh_key(self.lmid)

        if not gitlab.get_gpg_keys():
            gitlab.add_gpg_key(self.lmid)

        if not utils.ssh_dir + self.lmid + "-gitlab" in utils.read("/home/hal/.ssh/config"):
            self.config_ssh_client()
