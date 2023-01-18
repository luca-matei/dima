<network>
    <name>%LMID</name>
    <bridge name="%LMID" stp="on" delay="0" />
    <forward mode="nat" />
    <ip address="%GATEWAY" netmask="%NETMASK">
        <dhcp>
            <range start="%LEASE_START" end="%LEASE_END" />
            %HOSTS
        </dhcp>
    </ip>
    <dns enable="no"/>
</network>
