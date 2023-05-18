class HostUtils:
    envs = {}
    services = {}
    domain = None
    knock_grace = 1  # One knock
    knocking_grace = 30  # After successful knocking

    def create_host(self, env:'str'="dev", alias:'str'=None, mem:'int'=1024, cpus:'int'=1, disk:'int'=5):
        self.__doc__ = Host.create_host.__doc__
        # To do: choose a pm and invoke create_host()
        host_dbid = dima.lmobjs["lm4"]

        dima.pools.get(host_dbid).create_host(env, alias, mem, cpus, disk)

    def preseed_host(self, hostname, net_id, ip, ssh_port, host=dima.host_lmid):
        log(f"Preseeding '{hostname}' ...", console=True)
        arch = "amd" # "386"
        iso_dir = f"{utils.tmp_dir}debian-{utils.debian_version}/"
        iso_file = f"{utils.res_dir}debian-{utils.debian_version}.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"
        tmp_iso = utils.tmp_dir + hostname + ".iso"

        if utils.isfile(tmp_iso, host=host, quiet=True):
            log(f"Removing {tmp_iso}", level=3)
            cmd(f"sudo rm {tmp_iso}", host=host)

        if utils.isfile(iso_dir, host=host, quiet=True):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir, host=host)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null", host=host)

        log("Creating preseed file ...")
        # utils.new_pass(64)
        net = dima.pools.get(net_id)
        preseed_config = utils.format_tpl("preseed.tpl", {
            "ip": ip,
            "netmask": net.netmask,
            "gateway": net.gateway,
            "dns": net.domain.dns.ip,
            "hostname": hostname,
            "domain_name": net.domain,
            "root_pass": crypt.crypt("test", salt=crypt.mksalt(method=crypt.METHOD_SHA512, rounds=1048576)),
            "username": "dima",
            "user_pass": crypt.crypt("test", salt=crypt.mksalt(method=crypt.METHOD_SHA512, rounds=1048576)),
            "packages": "sudo openssh-server build-essential python3 python3-dev python3-venv python3-pip postgresql libpq-dev openssl nginx supervisor git curl wget gnupg2",
            "ssh_key": utils.read(utils.ssh_dir + hostname + ".pub"),
            "ssh_port": ssh_port,
            })

        utils.write(preseed_file, preseed_config, host=host)

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
            ]), host=host)

        """
        # Adding the preseed file to Initrd
        log("Adding preseed file ...")
        cmd(f"chmod +w {iso_dir}install.{arch}/")
        cmd(f"gunzip {iso_dir}install.{arch}/initrd.gz")
        cmd(f"echo {preseed_dir}preseed.cfg | cpio -H newc -o -A -F {iso_dir}install.{arch}/initrd")
        cmd(f"gzip {iso_dir}install.{arch}/initrd")
        cmd(f"chmod -w -R {iso_dir}install.{arch}/")
        """

        # Regenerating md5sum.txt
        log("Regenerating md5sum ...")
        cmd(f"chmod +w {iso_dir}md5sum.txt", host=host)
        cmd(f"md5sum `find {iso_dir} -follow -type f` > {iso_dir}md5sum.txt", host=host)

        md5sum = utils.read(iso_dir + "md5sum.txt", host=host)
        md5sum = md5sum.replace(iso_dir, "./")
        utils.write(iso_dir + "md5sum.txt", md5sum, host=host)

        cmd(f"chmod -w {iso_dir}md5sum.txt", host=host)

        log(f"Creating {hostname}.iso ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {tmp_iso} {iso_dir[:-1]}", host=host)

        if utils.isfile(iso_dir, host=host, quiet=True):
            log(f"Removing {iso_dir} ...", level=3)
            cmd("sudo rm -r " + iso_dir, host=host)

        log(f"Preseeded ISO image for '{hostname}' stored at '{tmp_iso}'", console=True)

    def transfer_file(self, from_path, to_path, from_host, to_host):
        transfer_path = utils.tmp_dir + "transfer/"
        if utils.isfile(transfer_path):
            cmd("rm -r " + transfer_path)

        dima.pools.get(from_host).retrieve_file(from_path, transfer_path)
        dima.pools.get(to_host).send_file(transfer_path, to_path)

utils.hosts = HostUtils()
