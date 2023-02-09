def download_resources(self):
    print("Downloading resources ...")
    if not os.path.isfile(f"{utils.res_dir}debian-{utils.debian_version}.iso"):
        print(f"Downloading Debian {utils.debian_version} ...")
        cmd(f"sudo -u hal wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-{utils.debian_version}-amd64-netinst.iso -q -O {utils.res_dir}debian-{utils.debian_version}.iso")
    else:
        print(f"Debian {utils.debian_version} is already installed!")

#####################

class Net:
    zones = ("ro", "us", "md", "bg", "rs", "hu", "ua", "sk", "cz", "dk", "de", "ie", "gr", "es", "fr", "hr", "it", "lu", "nl", "at", "pl", "pt", "sl", "fi", "se", "is", "no", "ch", "uk", "me", "mk", "al", "tr", "ba", "nz")

    def __init__(self, name):
        self.name = name

    def lmwhite(self):
        nft = ["set whiteip4 {\ntype ipv4_addr\nflags interval, constant\nelements = {\n"]
        for z in self.zones:
            cmd(f"wget -O white.zone http://ipverse.net/ipblocks/data/countries/{z}.zone")
            with open("white.zone", mode='r', encoding='utf-8') as f:
                ranges = f.readlines()

            for r in ranges:
                if not r or r.startswith("#"):
                    continue
                nft.append(f"{r[:-1]},\n")

        nft.append("}\nauto-merge\n}")

        with open("white-ipv4.nft", mode='w', encoding='utf-8') as f:
            f.write(''.join(nft))
