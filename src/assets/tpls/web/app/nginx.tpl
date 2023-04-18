server {
    listen 80;
    server_name %DOMAIN%;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name %DOMAIN%;
    keepalive_timeout 70;

    ssl_certificate      %SSL_DIR%pubkey.pem; # fullchain.pem
    ssl_certificate_key  %SSL_DIR%privkey.pem; # privkey.pem
    ssl_protocols TLSv1.3;

    ssl_prefer_server_ciphers on;
    ssl_ciphers "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256";

    ssl_session_timeout 30m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    ssl_dhparam %HAL_SSL_DIR%dhparam.pem;
    ssl_ecdh_curve secp521r1:secp384r1;

    ssl_stapling %OCSP%;
    ssl_stapling_verify %OCSP%;
    ssl_trusted_certificate %SSL_DIR%pubkey.pem; # fullchain.pem
    resolver 1.1.1.1 1.0.0.1 [2606:4700:4700::1111] [2606:4700:4700::1001] valid=300s;
    resolver_timeout 5s;

    add_header Content-Security-Policy "default-src 'none'; frame-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; font-src 'self';base-uri 'self';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Xss-Protection "1; mode=block" always;

    error_page 403                /http/403;
    error_page 404                /http/404;
    error_page 500 502 503 504    /http/50x;

    location /http/ {
        internal;
    }

    if ($request_method !~ ^(GET|HEAD|POST)$ ) {
        return 405;
    }

    location /commons/ {
        alias %RES_DIR%web/;
    }

    location /assets/ {
        valid_referers none blocked %DOMAIN% *.%DOMAIN%;
        if ($invalid_referer) {
            return 403;
        }
        root %REPO_DIR%src;
    }

    location ~ ^(\/robots\.txt|\/sitemap\.xml|\/favicon\.ico)$ {
        log_not_found off;
        access_log off;
        root %REPO_DIR%src/assets;
    }

    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:%PORT%;
    }

    access_log /var/log/nginx/%LMID%.acc.log;
    error_log /var/log/nginx/%LMID%.err.log warn;
}
