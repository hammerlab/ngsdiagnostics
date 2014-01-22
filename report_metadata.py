#!/usr/bin/python

import re
import sys
import datetime
import sqlite3
from optparse import OptionParser


def main(argv):
    parser = OptionParser(usage="usage: %prog <gatk log> <sqlite db>")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Wrong number of arguments")
    logfile = args[0]
    sqlitedb_filename = args[1]
    inf = open(logfile, 'r')
    run_time_pattern = re.compile("Date/Time: (\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2})")
    run_args_pattern = re.compile("Program Args: (.*)$")
    parsed_run_time = False
    parsed_run_args = False
    run_date = ''
    run_args = ''
    for line in [x.rstrip('\n') for x in inf.readlines()]: 
        m = run_time_pattern.search(line)
        if m:
            run_date = m.group(1)
            parsed_run_time = True
        m = run_args_pattern.search(line)
        if m:
            run_args = m.group(1)
            parsed_run_args = True
        if parsed_run_args and parsed_run_time:
            break

    if parsed_run_args and parsed_run_time:
        print "Timestamp for this run: " + run_date
        createRunMetadataIfDoesNotExist(run_date, run_args, sqlitedb_filename)


# Copied from stack overflow
def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    td = dt - epoch
    since_last =  (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    return since_last

def createRunMetadataIfDoesNotExist(run_date, run_args, sqlitedb_filename):
    seconds_since_epoch = unix_time(datetime.datetime.strptime(run_date, '%Y/%m/%d %H:%M:%S'))
    
    db = sqlite3.connect(sqlitedb_filename)
    c = db.cursor()
    
    try:
        c.execute("insert into run_timing_metadata (run_timestamp, run_args) values(?, ?)", (seconds_since_epoch, run_args))
    except sqlite3.IntegrityError as err:
        print "Run metadata (args, timestamp) already existed."

    db.commit()
    db.close()
    
if __name__=='__main__': 
	main(sys.argv)
