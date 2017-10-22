#!/bin/bash
crontab <<EOF
# restart musicserver just after 3am, rolls logs
05 03 * * * /home/pi/musicserver/scripts/musicserver --init /var/run/musicsever.pid >/tmp/musicserver.out 2>&1
EOF
