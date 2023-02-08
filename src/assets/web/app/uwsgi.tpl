[uwsgi]
socket = 127.0.0.1:%PORT
chdir = %APP_DIR
virtualenv = %PROJECTS_DIRvenv
module = app:application
master = true
processes = 1
uid = www-data
gid = www-data
harakiri = 30
post-buffering = 32768
buffer-size = 32768
vacuum = true
pidfile = %PROJECTS_DIRpids/%LMID.pid
logfile = %LOG_FILE
