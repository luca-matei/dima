subnet %SUBNET% netmask %NETMASK% {
    range      %LEASE_START%      %LEASE_END%;
    option routers                %GATEWAY%;
    option broadcast-address      %BROADCAST%;
    option domain-name            "%DOMAIN%";
    option domain-name-servers    %DNS%;
}
