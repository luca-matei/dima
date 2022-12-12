Port %PORT
AddressFamily inet
ListenAddress 0.0.0.0

Protocol 2

HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key

KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,hmac-sha2-512,hmac-sha2-256,umac-128@openssh.com

SyslogFacility AUTH
LogLevel VERBOSE

LoginGraceTime 32
PermitRootLogin no
StrictModes yes
MaxAuthTries 2
MaxSessions 2

PubkeyAuthentication yes
AuthorizedKeysFile    .ssh/authorized_keys
AuthorizedPrincipalsFile none
AuthorizedKeysCommand none
AuthorizedKeysCommandUser nobody

HostbasedAuthentication no
IgnoreUserKnownHosts yes
IgnoreRhosts yes

PasswordAuthentication no
PermitEmptyPasswords no

ChallengeResponseAuthentication no

# Kerberos options
#KerberosAuthentication no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes
#KerberosGetAFSToken no

# GSSAPI options
#GSSAPIAuthentication no
#GSSAPICleanupCredentials yes

UsePAM yes

AllowAgentForwarding no
AllowTcpForwarding no
AllowStreamLocalForwarding no
GatewayPorts no
X11Forwarding no
PrintMotd no
PrintLastLog no
TCPKeepAlive no
PermitUserEnvironment no
Compression no
ClientAliveInterval 0
ClientAliveCountMax 900
UseDNS no
PidFile /run/sshd.pid
MaxStartups 2
PermitTunnel no
ChrootDirectory none
VersionAddendum none
AllowGroups sshusers

Subsystem    sftp    /usr/lib/openssh/sftp-server
