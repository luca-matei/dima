#!/bin/bash

xhost SI:localuser:dima
sudo -u dima python3 /home/dima/projects/%LMID/src/make.py
sudo -u dima python3 /home/dima/projects/%LMID/src/app/app.py "$@"
