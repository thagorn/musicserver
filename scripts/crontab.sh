#!/bin/bash
crontab <<EOF
# restart musicserver just after midnight, rolls logs
05 00 * * * /home/pi/musicserver/scripts/musicserver >/tmp/musicserver.out 2>&1
EOF
