subnet %SUBNET% netmask %NETMASK% {
    range    %LEASE_START%    %LEASE_END%;
    option routers              %GATEWAY%;
    option broadcast-address    %BROADCAST%;
}
