$TTL 86400

@      IN    SOA    ns1.%DNS_DOMAIN%. hostmaster.%DNS_DOMAIN%. (
                    %SERIAL%
                      604800
                       86400
                     2419200
                       86400 )

@       IN    NS     ns1.%DNS_DOMAIN%.
@       IN    NS     ns2.%DNS_DOMAIN%.
;@       IN    MX     mail.%MAIL_DOMAIN%.

ns1        IN    A      %DNS_IP%
ns2        IN    A      %DNS_IP%
%DOMAIN_RECORDS%
%SUBDOMAIN_RECORDS%
