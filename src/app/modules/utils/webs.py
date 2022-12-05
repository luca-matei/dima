class WebUtils:
    modules = {}

    def generate_dh(self):
        if os.path.isfile(utils.ssl_dir + "dhparam.pem"):
            log("DH parameters are already in place!")
            yes = utils.yes_no("Purge them?")

            if yes: cmd(f"rm -r {utils.ssl_dir}dhparam.pem")
            else: return

        log("Generating DH params. This may take a while ...", console=True)
        cmd(f"openssl dhparam -out {utils.ssl_dir}dhparam.pem -5 4096")

    def config_nginx(self):
        log(f"Configuring Nginx ...")
        cmd(f"cp {src_dir}assets/tpls/web/nginx.conf /etc/nginx/nginx.conf")
        cmd("systemctl restart nginx")

utils.webs = WebUtils()
