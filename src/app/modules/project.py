class Project(lmObj):
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        self.repo_dir = utils.projects_dir + self.lmid + '/'
        self.log_file = utils.logs_dir + self.lmid + ".log"

        query = "select dev_host, dev_version, prod_host, prod_version from project.projects where lmobj=%s;"
        params = self.dbid,
        self.dev_host_id, self.dev_version, self.prod_host_id, self.prod_version = dima.db.execute(query, params)[0]

        self.dev_host = dima.lmobjs[self.dev_host_id][0]
        self.prod_host = dima.lmobjs[self.prod_host_id][0]

        self.check_project()

    def check_project(self):
        if not utils.isfile(self.repo_dir, host=self.dev_host):
            if utils.confirm(f"'{self.name}' project repository doesn't exist on '{self.dev_host}'! Clone it from Gitlab?"):
                dima.pools.get(self.dev_host_id).clone_repo(self.lmid)
            else:
                log(f"Project '{self.name}' isn't on a dev machine!", level=4, console=True)
                return

        self.get_token()

    def get_token(self):
        token_file = self.repo_dir + "project_token.txt"
        if not utils.isfile(token_file, host=self.dev_host):
            token = gitlab.create_token(self.dev_host, self.lmid)
            utils.write(token_file, token, host=self.dev_host)
        else:
            return utils.read(token_file, host=self.dev_host)

    def save(self, message:'str'="Updated files"):
        log(f"Saving '{self.name}' on Gitlab ...", console=True)
        git_cmd = f"git --git-dir={self.repo_dir}.git/ --work-tree={self.repo_dir} " + "{}"
        cmd(git_cmd.format(f"add {self.repo_dir}*"), host=self.dev_host)
        cmd(git_cmd.format(f"commit -m '{message}'"), host=self.dev_host)
        cmd(git_cmd.format("push"), host=self.dev_host)
        log(f"Saved '{self.name}' on Gitlab", console=True)
