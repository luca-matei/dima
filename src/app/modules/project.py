class Project:
    def __init__(self, dbid):
        lmObj.__init__(self, dbid)

        self.repo_dir = utils.projects_dir + self.lmid + '/'
        self.log_file = utils.logs_dir + self.lmid + ".log"

    def save(self, message="Updated files"):
        # Will be replaced with the API method
        log(f"Saving {self.name} on Gitlab ...")
        git_cmd = f"git --git-dir={self.repo_dir}.git/ --work-tree={self.repo_dir} " + "{}"
        cmd(git_cmd.format(f"add {self.repo_dir}*"))
        cmd(git_cmd.format(f"commit -m '{message}'"))
        cmd(git_cmd.format("push"))
