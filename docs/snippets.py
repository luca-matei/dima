# This will go somewhere else
def download_resources(self):
    print("Downloading resources ...")
    if not os.path.isfile(f"{utils.res_dir}debian-{utils.debian_version}.iso"):
        print(f"Downloading Debian {utils.debian_version} ...")
        cmd(f"sudo -u hal wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-{utils.debian_version}-amd64-netinst.iso -q -O {utils.res_dir}debian-{utils.debian_version}.iso")
    else:
        print(f"Debian {utils.debian_version} is already installed!")
