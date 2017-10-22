#!/bin/bash
HOME=/home/pi
BASE=$HOME/musicserver/scripts
mkdir -p $HOME/mediaplayer
$BASE/crontab.sh
sudo ln -s $BASE/init/musicserver /etc/init.d
sudo update-rc.d musicserver defaults
sudo service musicserver start
