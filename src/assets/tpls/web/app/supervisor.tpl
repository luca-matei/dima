[program:%LMID%]
command = %PROJECTS_DIR%venv/bin/uwsgi --ini %APP_DIR%uwsgi.ini
autostart = true
autorestart = true
user = www-data
stopsignal = QUIT
environment=LANG="en_US.utf8", LC_ALL="en_US.UTF-8", LC_LANG="en_US.UTF-8"
stderr_logfile=/var/log/supervisor/%LMID%.err.log
stdout_logfile=/var/log/supervisor/%LMID%.out.log
