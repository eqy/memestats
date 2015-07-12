#!/bin/sh
while true;
do
	time python3 memestats.py
	cp desktop /var/www/html/
	cp battlestation /var/www/html/
	cp koptek.txt /var/www/html/
	echo $(date) > /var/www/html/memetime
	sleep 30
done
