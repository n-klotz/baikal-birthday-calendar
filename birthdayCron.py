#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import vobject
from datetime import datetime, timedelta
import hashlib
import calendar
import os.path

##########
# CONFIG #
##########

sqlpath = '/var/www/baikal/Specific/db/db.sqlite'
calendaruri  = 'birthdays'
calendarname = 'Birthdays'
calendartz = 'Europe/Berlin'
calendardesc = 'Automatically populated birthday calendar'
calendarcolor = '#A6DCE9'
bdaytext = 'Birthday of '

### END CONFIG ###

# dates
now = datetime.utcnow()
nowts = calendar.timegm(now.timetuple())

# db connections
db = sqlite3.connect(sqlpath)
db.text_factory = str

read_cur  = db.cursor()
write_cur = db.cursor()

# Load synctokens of addressbooks and consolidate into one entry per principal
current_addressbook_synctokens = {}
read_cur.execute('SELECT principaluri, synctoken FROM addressbooks ORDER BY id ASC')
for addressbook in read_cur.fetchall():
    if addressbook[0] not in current_addressbook_synctokens:
        current_addressbook_synctokens[addressbook[0]] = str(addressbook[1])
    else:
        current_addressbook_synctokens[addressbook[0]] = current_addressbook_synctokens[addressbook[0]]+str(addressbook[1])

# Get principals from DB
read_cur.execute('SELECT uri FROM principals')
for principal in read_cur.fetchall():
    # Set uri of principal
    uri = principal[0]

    # Get birthdays calendar from principal
    read_cur.execute('SELECT id FROM calendars WHERE principaluri = ? and uri = ?', [uri, calendaruri])
    row = read_cur.fetchone()

    if row == None:
        # Create birthdays calendar if not existing
        var = [uri, calendarname, calendaruri, 1, calendardesc, 0, calendarcolor, calendartz, "VEVENT"]
        write_cur.execute('INSERT INTO calendars (principaluri, displayname, uri, synctoken, description, calendarorder, calendarcolor, timezone, components) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', var)
        calendarid = write_cur.lastrowid
    else:
        calendarid = row[0]

    # Clear calendar first
    write_cur.execute('DELETE FROM calendarobjects WHERE calendarid = ?', [calendarid])

    read_cur.execute('SELECT c.carddata, c.uri FROM cards as c JOIN addressbooks as a ON c.addressbookid = a.id WHERE a.principaluri = ?', [uri])
    for row in read_cur.fetchall():
        card = vobject.readOne(row[0])
        carduri = row[1]

        if hasattr(card, 'bday'):
            bday = datetime.strptime(card.bday.value, '%Y-%m-%d').date()
            ca = vobject.newFromBehavior('vcalendar')

            # Create event
            ev = ca.add('vevent')
            ev.add('summary').value = bdaytext+card.fn.value
            ev.add('dtstart').value = bday
            ev.add('dtend').value = bday+timedelta(days=1)
            ev.add('class').value = "public"
            ev.add('created').value = now
            ev.add('dtstamp').value = now
            ev.add('last-modified').value = now
            ev.add('rrule').value = "FREQ=YEARLY;BYMONTHDAY="+str(bday.day)+";BYMONTH="+str(bday.month);
            ev.add('transp').value = "TRANSPARENT"
            ev.add('categories').value = ["Birthday"]
            ev.add('x-microsoft-cdo-alldayevent').value = "TRUE"

            # Create alarm
            al = ev.add('valarm')
            al.add('action').value = "Display"
            al.add('trigger;related=end').value = "-PT16H"

            data = ca.serialize();
            etag = hashlib.md5(data).hexdigest()
            size = len(data)
            newuri = str(carduri[:-4])+'.ics'

            # Insert data into DB
            var = [data, newuri, calendarid, nowts, etag, size, 'VEVENT', nowts, nowts+300000000]
            write_cur.execute('INSERT INTO calendarobjects (calendardata, uri,  calendarid, lastmodified, etag, size, componenttype, firstoccurence,lastoccurence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', var)

            # Debug Output
            # print "Inserted new entry with title "+card.fn.value+"."

    # Update synctoken in birthday calendar (to indicate changes)
    write_cur.execute('UPDATE calendars SET synctoken = synctoken + 1 WHERE id = ?', [calendarid])

db.commit()
read_cur.close()
write_cur.close()
db.close()
