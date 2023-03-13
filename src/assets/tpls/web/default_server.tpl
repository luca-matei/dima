server {
    listen 80 default_server;
    server_name _;

    error_page 403                /status/403.html;
    error_page 404                /status/404.html;
    error_page 500 502 503 504    /status/50x.html;

    location /status/ {
        root %PROJECTS_DIR%default_server;
    }

    location / {
        return 444;
    }

}
