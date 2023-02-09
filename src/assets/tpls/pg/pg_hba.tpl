local   all             postgres                                peer
local   all             hal                                     peer
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
%REMOTE_AUTH
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            scram-sha-256
