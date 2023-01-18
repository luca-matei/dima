class HostUtils:
    envs = {}

    def preseed_host(self, hostname, net_id, ip):
        arch = "amd" # "386"
        iso_dir = f"{utils.tmp_dir}debian-{utils.debian_version}/"
        print(iso_dir)
        iso_file = f"{hal.src_dir}assets/debian-{utils.debian_version}.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"
        tmp_iso = utils.tmp_dir + hostname + ".iso"

        if os.path.isfile(tmp_iso):
            log(f"Removing {tmp_iso}", level=3)
            cmd(f"sudo rm {tmp_iso}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null")

        log("Creating preseed file ...")
        # utils.new_pass(64)
        net = hal.pools.get(net_id)
        preseed_config = utils.format_tpl("preseed.tpl", {
            "ip": ip,
            "netmask": net.netmask,
            "gateway": net.gateway,
            "dns": hal.pools.get(net.dns_id).ip,
            "hostname": hostname,
            "domain_name": net.domain,
            "root_pass": "test",
            "root_pass_hash": "",
            "user_fullname": "hal",
            "username": "hal",
            "user_pass": "test",
            "user_pass_hash": ""
            })

        utils.write(preseed_file, preseed_config)

        log("Configuring boot options ...")
        utils.write(isolinux_file, '\n'.join([
            "path",
            "label lminstall",
            "    menu label ^Automated LM Install",
            "    kernel /install.amd/vmlinuz",
            "    append auto=true priority=critical vga=788 file=/cdrom/preseed.cfg initrd=/install.amd/initrd.gz --- quiet",
            "default lminstall",
            "prompt 0",
            "timeout 1",
            ]))

        """
        # Adding the preseed file to the Initrd
        log("Adding preseed file ...")
        cmd(f"chmod +w {iso_dir}install.{arch}/")
        cmd(f"gunzip {iso_dir}install.{arch}/initrd.gz")
        cmd(f"echo {preseed_dir}preseed.cfg | cpio -H newc -o -A -F {iso_dir}install.{arch}/initrd")
        cmd(f"gzip {iso_dir}install.{arch}/initrd")
        cmd(f"chmod -w -R {iso_dir}install.{arch}/")
        """

        # Regenerating md5sum.txt
        log("Regenerating md5sum ...")
        cmd(f"chmod +w {iso_dir}md5sum.txt")
        cmd(f"md5sum `find {iso_dir} -follow -type f` > {iso_dir}md5sum.txt")

        md5sum = utils.read(iso_dir + "md5sum.txt")
        md5sum = md5sum.replace(iso_dir, "./")
        utils.write(iso_dir + "md5sum.txt", md5sum)

        cmd(f"chmod -w {iso_dir}md5sum.txt")

        log(f"Creating {lmid}.iso ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {tmp_iso} {iso_dir[:-1]}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir)

        log(f"Preseeded ISO image for {hostname} stored at {self.tmp_iso}", console=True)

    def register_host(self, mode=None):
        # This host can only be a PM
        opts = {
            1: "Create ISO image",
            2: "Create install script",
            }

        lmid = hal.next_lmid()
        alias = None

        while alias != "":
            alias = input("Preferred hostname (Press Enter to skip): ")
            if hal.check_alias(alias):
                break

        hostname = alias if alias else lmid

        mode = utils.select_opt(opts)

        if mode == 1:
            ip = utils.nets.get_free_ip(hal.net_dbid)
            self.preseed_host(hostname, hal.net_dbid, ip)

        elif mode == 2:
            pass

utils.hosts = HostUtils()
