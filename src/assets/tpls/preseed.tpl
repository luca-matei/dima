#_preseed_V1
#### Preseeding Debian Bullseye for dev VMs

### Localization
d-i debian-installer/locale string en_US
d-i debian-installer/language string en
d-i debian-installer/country string RO
#d-i debian-installer/locale string en_US.UTF-8
d-i localechooser/supported-locales multiselect en_US.UTF-8

### Keyboard
d-i keyboard-configuration/xkb-keymap select us

### Network configuration
d-i netcfg/choose_interface select auto
d-i netcfg/use_dhcp string true
d-i netcfg/link_wait_timeout string 10
d-i netcfg/dhcp_timeout string 60

#d-i netcfg/disable_autoconfig boolean true
#d-i netcfg/dhcp_failed note
#d-i netcfg/dhcp_options select Configure network manually

# IPv4
#d-i netcfg/get_ipaddress string %IP
#d-i netcfg/get_netmask string %NETMASK
#d-i netcfg/get_gateway string %GATEWAY
#d-i netcfg/get_nameservers string %DNS
#d-i netcfg/confirm_static boolean true

#d-i netcfg/get_hostname string unassigned-hostname
#d-i netcfg/get_domain string unassigned-domain
d-i netcfg/get_hostname string %HOSTNAME
d-i netcfg/get_domain string %DOMAIN_NAME
d-i netcfg/hostname string %HOSTNAME
d-i netcfg/wireless_wep string

### Mirror Settings
d-i mirror/country string RO
d-i mirror/http/hostname string deb.debian.org
d-i mirror/http/directory string /debian/
d-i mirror/http/proxy string

### Account setup
d-i passwd/root-password password %ROOT_PASS
d-i passwd/root-password-again password %ROOT_PASS
#d-i passwd/root-password-crypted password [%ROOT_PASS_HASH]

d-i passwd/user-fullname string %USER_FULLNAME
d-i passwd/username string %USERNAME
d-i passwd/user-password password %USER_PASS
d-i passwd/user-password-again password %USER_PASS
#d-i passwd/user-password-crypted password [%USER_PASS_HASH]

### Clock
d-i clock-setup/utc boolean true
d-i time/zone string Europe/Bucharest
d-i clock-setup/ntp boolean true

### Partitioning
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select dev-scheme
d-i partman-auto/expert_recipe string               \
    dev-scheme ::                                   \
        500 10000 1000000 ext4                      \
            $primary{ }                             \
        	$bootable{ }                            \
        	method{ format }                        \
        	format{ }                               \
        	use_filesystem{ }                       \
        	filesystem{ ext4 }                      \
        	mountpoint{ / }                         \
        .                                           \
        64 512 300% linux-swap                      \
            method{ swap }                          \
            format{ }                               \
        .
#d-i partman-basicfilesystems/no_mount_point boolean false
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true

### Apt Setup
d-i apt-setup/cdrom/set-first boolean false
d-i apt-setup/cdrom/set-next boolean false
d-i apt-setup/cdrom/set-failed boolean false
d-i apt-setup/services-select multiselect security, updates
d-i apt-setup/security_host string security.debian.org
#d-i apt-setup/non-free boolean true
#d-i apt-setup/contrib boolean true
#d-i apt-setup/disable-cdrom-entries boolean true
#d-i apt-setup/enable-source-repositories boolean true

### Package selection
tasksel tasksel/first multiselect standard
#d-i pkgsel/include string sudo openssh-server build-essential python3 python3-dev python3-venv postgresql libpq-dev nginx supervisor
d-i pkgsel/upgrade select safe-upgrade
d-i pkgsel/update-policy select none
d-i pkgsel/updatedb boolean true
popularity-contest popularity-contest/participate boolean false

### GRUB
d-i grub-installer/only_debian boolean true
d-i grub-installer/bootdev string default
#d-i grub-installer/password password r00tme
#d-i grub-installer/password-again password r00tme
#d-i grub-installer/password-crypted password [MD5 hash]

### Finishing up the installation
d-i finish-install/reboot_in_progress note

#d-i preseed/late_command string wget http://
#$ sudo groupadd sshusers
#$ sudo usermod -aG sshusers neon
