server {
    listen 80;
    server_name %FROM%;
    return 301 https://%TO%;
}
