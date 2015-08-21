#!/bin/sh
while true;
do
    time python3 memestats.py & sleep 300; kill $!
    cp desktop /var/www/html/
    cp battlestation /var/www/html/
    cp thinkpad /var/www/html/
	cp koptek.txt /var/www/html/
    cp name /var/www/html/
	echo $(date) > /var/www/html/memetime
	sleep 120
done
