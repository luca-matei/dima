########
## This file is automatically managed by Hal.
## Any manual modification to this file might be lost!
########

Include /etc/ssh/ssh_config.d/*.conf

Host *
    SendEnv LANG LC_*
    HashKnownHosts yes
    GSSAPIAuthentication yes
