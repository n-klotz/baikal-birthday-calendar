baikal-birthday-calendar
========================

Python script to automatically create birthday calendar entries for a baikal server (http://baikal-server.com).

Tested with baikal 0.4.6 and python 2.7.9 on Debian 8.6. Works only with SQLite backend.

This script is based on a previous version by mcwolle for baikal and MySQL.

Installation
========================
- Copy script e.g. to /var/www/baikal/birthday.cron/
- Modify the script and change the following parameters:  
    * filepath to sqlite database (sqlpath)
    * name of the birthday calendar (calendaruri)
    * displayed name of the birthday calendar (calendarname)
    * time zone (calendartz)
    * calendar description (calendardesc)
    * displayed calendar color (calendarcolor)
- Add the script as cron task

Credits 
========================
- mcwolle : https://github.com/mcwolle/baikal-birthday-calendar
- funkfux : https://github.com/fruux/Baikal/issues/38
