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
    parser = OptionParser(
        usage="""usage: %prog <file with list of logfile paths, \
one per line> <sqlite db>""")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.error("Wrong number of arguments")
    logfiles_list_filename = args[0]
    sqlitedb_filename = args[1]

    logfiles = open(logfiles_list_filename)
    db = sqlite3.connect(sqlitedb_filename)
    c = db.cursor()
    for one_logfile in logfiles:
        components = one_logfile.strip().split(" ")
        timestamp = components[5] + " " + re.sub("\.[0-9]+","", components[6])
        pathname = components[8]
        logfile_date = datetime.datetime.strptime(timestamp, 
                                                  "%Y-%m-%d %H:%M:%S")
        
        try:
            c.execute("""\
            INSERT INTO log_file_paths (pathname, run_timestamp)
            VALUES                     (?, ?)""",
                      (pathname, utils.unix_time(logfile_date)))
            db.commit()
        except sqlite3.IntegrityError as err:
            print("Logfile already existed.")
    db.close()
if __name__=='__main__': 
	main(sys.argv)
