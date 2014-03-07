#!/usr/bin/python

#
# Copyright (c) 2014. Mount Sinai School of Medicine
#

import datetime
import re
import sqlite3
import sys
import utils

from optparse import OptionParser


def main(argv):
    parser = OptionParser(usage="usage: %prog <gatk log> <sqlite db>")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Wrong number of arguments")
    logfile = args[0]
    sqlitedb_filename = args[1]
    row_id = report_metadata_to_db(logfile, sqlitedb_filename)
    print(row_id)

def report_metadata_to_db(logfile, sqlitedb_filename):
    inf = open(logfile, 'r')
    run_time_pattern = re.compile("Date/Time: (\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2})")
    run_args_pattern = re.compile("Program Args: (.*)$")
    sample_pattern = re.compile("SM:([^\\\\]+)")
    run_date = ''
    run_args = ''
    sample = ''
    print(logfile)
    for line in [x.rstrip('\n') for x in inf.readlines()]: 
        m = run_time_pattern.search(line)
        if m:
            run_date = m.group(1)
        m = run_args_pattern.search(line)
        if m:
            run_args = m.group(1)
        m = sample_pattern.search(line)
        if m:
            sample = m.group(1)
        if run_date and run_args and sample:
            print("Timestamp for this run: " + run_date)
            print("Sample for this run: " + sample) 
            row_id = createRunMetadataIfDoesNotExist(run_date, run_args, sample, sqlitedb_filename)
            break
    inf.close()
    return row_id

def createRunMetadataIfDoesNotExist(run_date, run_args, sample, sqlitedb_filename):
    seconds_since_epoch = utils.unix_time(
        datetime.datetime.strptime(run_date, '%Y/%m/%d %H:%M:%S'))
    
    db = sqlite3.connect(sqlitedb_filename)
    c = db.cursor()
    
    try:
        c.execute("""\
        INSERT INTO run_timing_metadata (run_timestamp, run_args, sample)
        VALUES      (?, ?, ?)""",
        (seconds_since_epoch, run_args, sample))
    except sqlite3.IntegrityError as err:
        print("Run metadata (args, timestamp, sample) already existed.")

    result = c.execute("""\
    SELECT rowid from run_timing_metadata 
    WHERE  run_timestamp = ? and run_args = ? and sample = ?
    """, (seconds_since_epoch, run_args, sample))
    row_id = result.fetchone()[0]
    db.commit()
    db.close()
    return row_id
    
if __name__=='__main__': 
	main(sys.argv)
