#!/usr/sbin/nft -f

flush ruleset

table ip firewall {
    set clients {
        type ipv4_addr
        flags timeout
    }

    set candidates {
        type ipv4_addr . inet_service
		flags timeout
    }

    chain input {
        type filter hook input priority 0; policy drop;

        ct state vmap { established: accept, related: accept, invalid: drop }
        tcp flags & (fin|syn|rst|ack) != syn ct state new counter drop
        icmp type echo-request limit rate over 1/second burst 5 packets drop
        icmp type { destination-unreachable, echo-reply, echo-request, source-quench, time-exceeded } accept

        iif "lo" accept
        iif != "lo" ip daddr 127.0.0.1/8 counter log prefix "[nftables] Dropped conns to lo not coming from lo" drop

        %KNOCK%
        %SERVICE_RULES%

        log prefix "[nftables] Input Denied: " flags ip options counter drop
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }
}

table netdev firewall {
    include "/etc/nft/bogons-ipv4.nft"
    include "/etc/nft/black-ipv4.nft"

    chain early_filter {
        type filter hook ingress device %IFACE% priority -500; policy accept;
        ip frag-off & 0x1fff != 0 counter drop
        #ip saddr @bogonsip4 counter drop # Comment just for dev machine
        #ip saddr == @blackip4 counter drop
        tcp flags & (fin|syn|rst|psh|ack|urg) == fin|syn|rst|psh|ack|urg counter drop
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0x0 counter drop
        tcp flags syn tcp option maxseg size 1-535 counter drop
    }
}

table ip6 firewall {
    chain input {
        type filter hook input priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy drop;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }
}
