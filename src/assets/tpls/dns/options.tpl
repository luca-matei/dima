options {
    directory "/var/cache/bind";
    dnssec-validation auto;

    auth-nxdomain no;
    listen-on port 53 { %IP%; };
    listen-on-v6 { none; };

    version "420.69";
    recursion no;
    querylog yes;

    allow-query { any; };
    allow-query-cache { none; };
    allow-transfer { none; };
    allow-recursion { none; };
};
