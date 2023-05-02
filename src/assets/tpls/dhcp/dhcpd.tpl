default-lease-time    64800;
max-lease-time        64800;
ddns-update-style     none;
log-facility          local7;
authoritative;

option domain-name            "%DOMAIN%";
option domain-name-servers    %DNS%;

include "/etc/dhcp/dhcp.d/subnets.conf";
include "/etc/dhcp/dhcp.d/hosts.conf";
