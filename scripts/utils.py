#!/usr/bin/python

#
# Copyright (c) 2014. Mount Sinai School of Medicine
#

import datetime

# Copied from stack overflow
def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    td = dt - epoch
    since_last =  (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    return since_last
