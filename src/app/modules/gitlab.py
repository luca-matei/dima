class Gitlab:
    # Line count git ls-files | xargs wc -l
    domain = None
    user = None

    def __init__(self):
        pass

    def get_token(self):
        token_file = hal.app_dir + 'personal_token.txt'

        if not utils.isfile(token_file):
            log("Getting Gitlab REST API token ...")
            print("Please enter Hal's Gitlab REST API token.")

            token = getpass.getpass("Token: ")
            utils.write(token_file, token)
            cmd("chmod 600 " + token_file)

            return token
        else:
            return utils.read(token_file)

    def request(self, host=hal.host_lmid, token=None, method="get", endpoint="", data={}):
        if not token: token = self.get_token()

        method = method.upper()
        if method not in ("GET", "POST", "PUT"):
            log(f"Invalid method '{method}'!", level=4)
            return {}

        curl = f"""curl -s --request {method} --header "PRIVATE-TOKEN: {token}" --header "Content-Type:application/json" --data '{json.dumps(data)}' --url "https://{self.domain}/api/v4{endpoint}" """

        response = cmd(curl, catch=True, host=host)
        return json.loads(response)

    def create_token(self, host_lmid, project_lmid):
        response = self.request(
            method = "post",
            endpoint = f"/projects/{self.user}%2F{project_lmid}/access_tokens",
            data = {
                "name": host_lmid,
                "scopes": ["api",],
                "access_level": 30,
                }
            )

        return response['token']

    def add_ssh_key(self, title, pubkey):
        data = {
            'title': title,
            'key': pubkey
            }

        self.request(
            host = hal.host_lmid,
            token = self.get_token(),
            method = "post",
            endpoint = "/user/keys",
            data = data
            )

    def add_gpg_key(self, email, pubkey):
        self.request(
            method = "post",
            endpoint = "/user/gpg_keys",
            data =  {'key': pubkey}
            )





    def add_email(self, email):
        self.request(
            method = "post",
            endpoint = "/user/emails",
            data = {'email': email}
            )

    def clone(self, lmid):
        log(f"Cloning {lmid} Gitlab repository ...", console=True)
        cmd(f"git clone git@{self.domain}:{self.user}/{lmid}.git {utils.projects_dir}{lmid}/", host=self.host_lmid)

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

        lmid = data['path']

        if self.get_projects(lmid):
            log(f"Gitlab repo '{lmid}' created!", console=True)
            return 1
        else:
            log(f"Couldn't create Gitlab repo '{lmid}'!", level=4, console=True)
            return 0

    def check(self):
        if not utils.isfile("/home/hal/.gitconfig"):
            self.config_git()

        if not gitlab.get_ssh_keys(self.lmid):
            gitlab.add_ssh_key(self.lmid)

        if not gitlab.get_gpg_keys():
            gitlab.add_gpg_key(self.lmid)

        if not utils.ssh_dir + self.lmid + "-gitlab" in utils.read("/home/hal/.ssh/config"):
            self.config_ssh_client()

gitlab = Gitlab()
