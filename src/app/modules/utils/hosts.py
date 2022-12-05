class HostUtils:
    envs = {}

    def next_guest(self):
        # To do: check storage and memory usage
        return hal.host_dbid
        return hal.db.execute("select id from lmobjs where lmid='lmg2';")[0][0]

    def create_guest(self, alias="", private=False):
        log(f"Creating new {hal.env} guest ...")

        lmid = hal.hutil.next_lmid('Guest')
        net_id, net, ip = hal.nutil.next_ip()

        if self.create_libvirt_guest(lmid, net_id, net, ip):
            # Getting mac address
            xml_file = hal.bay_dir + 'guest.xml'
            cmd(f"sudo cp /etc/libvirt/qemu/{lmid}.xml {xml_file}")
            cmd(f"sudo chown {hal.user}:{hal.user} {xml_file}")
            mac = re.compile("<mac address='(.*?)'/>").search(util.read(xml_file)).group(1)

            dbid = hal.hutil.insert_lmobj(lmid, 'Guest', alias)

            query = "insert into guests (lmobj, net, mac, ip, env) values (%s, %s, %s, %s, %s);"
            params = dbid, net_id, mac, ip, hal.envs.get(hal.env),
            hal.db.execute(query, params)

            hal.db.execute("update nets set vacant = vacant-1 where lmobj=%s", (net_id,))

            hal.nutil.config_dhcp()

    def create_libvirt_guest(self, lmid, net_id, net, ip):
        self.preseed(lmid, net, ip)

        # https://manpages.debian.org/testing/virtinst/virt-install.1.en.html
        cmd(f"sudo virt-install " + ' '.join([
            f"--name {lmid}",
            "--memory 1024",
            "--vcpus 1",
            f"--cdrom {hal.bay_dir}guest.iso",
            "--os-variant generic",
            f"--disk {hal.guests_dir + lmid}.qcow2,size=2,format=qcow2,cache=none",
            f"--network network={hal.lmobjs[net_id][0]}",
            "--noautoconsole",
            ]))

        if util.isfile(f"/etc/libvirt/qemu/{lmid}.xml"):
            return 1
        else:
            log(f"Couldn't create {lmid} guest!", level=4, console=True)
            return 0

    def preseed(self, lmid, net, ip):
        arch = "amd" # "386"
        iso_dir = hal.bay_dir + "debian/"
        iso_file = hal.assets_dir + "debian.iso"
        preseed_file = iso_dir + "preseed.cfg"
        isolinux_file = iso_dir + "isolinux/isolinux.cfg"

        if util.isfile(hal.bay_dir + "guest.iso"):
            cmd(f"sudo rm {hal.bay_dir}guest.iso")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...")
            cmd("sudo rm -r " + iso_dir)

        log("Extracting files from iso ...")
        cmd(f"7z x -bd -o{iso_dir} {iso_file} > /dev/null")

        log("Creating preseed file ...")
        # util.new_pass(64)
        preseed_config = util.read(hal.tpl_dir + "preseed.tpl")\
            .replace("%IP", ip) \
            .replace("%NETMASK", str(net.netmask)) \
            .replace("%GATEWAY", str(net[1])) \
            .replace("%DNS", hal.nutil.dns) \
            .replace("%HOSTNAME", lmid) \
            .replace("%DOMAIN_NAME", hal.nutil.host_domain) \
            .replace("%ROOT_PASS", "test") \
            .replace("%ROOT_PASS_HASH", "") \
            .replace("%USER_FULLNAME", "hal") \
            .replace("%USERNAME", "hal") \
            .replace("%USER_PASS", "test") \
            .replace("%USER_PASS_HASH", "")

        util.write(preseed_file, preseed_config)

        log("Configuring boot options ...")
        util.write(isolinux_file, '\n'.join([
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

        md5sum = util.read(iso_dir + "md5sum.txt")
        md5sum = md5sum.replace(iso_dir, "./")
        util.write(iso_dir + "md5sum.txt", md5sum)

        cmd(f"chmod -w {iso_dir}md5sum.txt")

        log(f"Creating {lmid} iso image ...")
        cmd(f"genisoimage -quiet -r -J -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {hal.bay_dir}guest.iso {iso_dir[:-1]}")

        if os.path.isdir(iso_dir):
            log(f"Removing {iso_dir} ...")
            cmd("sudo rm -r " + iso_dir)

utils.hosts = HostUtils()
