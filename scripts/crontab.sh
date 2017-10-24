#!/bin/bash
crontab <<EOF
# restart musicserver just after 3am, rolls logs
05 03 * * * /home/pi/musicserver/scripts/musicserver --init /var/run/musicserver/pid >/tmp/musicserver.out 2>&1
# hourly pre fetch podcasts
28 * * * * flock --exclusive --nonblock /var/run/musicserver/PREFETCH_LOCK /home/pi/musicserver/scripts/prefetch.py >>/tmp/pre_fetch.out 2>&1
EOF
