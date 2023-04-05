#!/bin/bash

xhost SI:localuser:hal
sudo -u hal python3 /home/hal/projects/%LMID/src/make.py "$@"
sudo -u hal python3 /home/hal/projects/%LMID/src/app/app.py "$@"
