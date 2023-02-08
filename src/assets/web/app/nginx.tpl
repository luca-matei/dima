#server {
#    listen 80;
#    server_name %NAME.%DOMAIN;
#    return 301 ## TO ADD
#}

server {
    listen 80;
    server_name %LMID.%DOMAIN;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name %LMID.%DOMAIN;
    keepalive_timeout 70;

    ssl_certificate      %SSL_DIRpubkey.pem; # fullchain.pem
    ssl_certificate_key  %SSL_DIRprivkey.pem; # privkey.pem
    ssl_protocols TLSv1.3;

    ssl_prefer_server_ciphers on;
    ssl_ciphers "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256";

    ssl_session_timeout 30m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    ssl_dhparam %HAL_SSL_DIRdhparam.pem;
    ssl_ecdh_curve secp521r1:secp384r1;

    ssl_stapling %OCSP;
    ssl_stapling_verify %OCSP;
    ssl_trusted_certificate %SSL_DIRpubkey.pem; # fullchain.pem
    resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001] valid=300s;
    resolver_timeout 5s;

    add_header Content-Security-Policy "default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; font-src 'self';base-uri 'self';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Xss-Protection "1; mode=block" always;

    if ($request_method !~ ^(GET|HEAD|POST)$ ) {
        return 405;
    }

    location /assets/ {
        valid_referers none blocked %DOMAIN *.%DOMAIN;
        if ($invalid_referer) {
            return 403;
        }
        root %REPO_DIRsrc;
    }

    location ~ ^(\/robots\.txt|\/sitemap\.xml|\/favicon\.ico)$ {
        log_not_found off;
        access_log off;
        root %REPO_DIRsrc/assets;
    }

    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:%PORT;
    }

    access_log /var/log/nginx/%LMID.acc.log;
    error_log /var/log/nginx/%LMID.err.log warn;
}
