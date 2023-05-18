$TTL 86400
$ORIGIN %ZONE%.

@      IN    SOA    ns1.%GLUE%. hostmaster.%GLUE%. (
                    %SERIAL%
                      604800
                       86400
                     2419200
                       86400 )

@       IN    NS     ns1.%GLUE%.
@       IN    NS     ns2.%GLUE%.
;@       IN    MX     mail.%GLUE%.

ns1        IN    A      %DNS_IP%
ns2        IN    A      %DNS_IP%
;mail       IN    A      %MAIL_IP%
%WEB_RECORDS%
%MAIL_RECORDS%
