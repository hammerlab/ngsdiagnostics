#!/usr/bin/python

#
# Copyright (c) 2013. Genome Bridge LLC
#
# Add per sample output (sample name, size of data, read counts)
# define schema (sample, sample stats, ...) in SQLite3 for tracking

import logging
import re
import sqlite3
import sys
import report_metadata
from collections import defaultdict

# Each line in the log file is scanned for one of these strings --
# these define the "steps" under which the time elapsed is aggregated.
steps = ['bwa mem', 'SortSam', 'RealignerTargetCreator', 'IndelRealigner',
         'MergeSamFiles', 'MarkDuplicates', 'BaseRecalibrator', 'PrintReads',
         'CalculateHsMetrics', 'CollectGcBiasMetrics', 'CollectMultipleMetrics',
         'ReduceReads', 'ContEst', 'UnifiedGenotyper', 'HaplotypeCaller',
         'VariantAnnotator', 'AnnotateCosegregation', 'AnnotateLikelyPathogenic',
         'VariantEval', 'org.broadinstitute.sting.tools.CatVariants']

# FunctionEdge (Starting | Done) regexp
# The value of the last capture group is the string which is used to match
# different functionedge lines across the logfile and determine
# the start/end time of each subtask.
patt = re.compile('INFO\\s+(\\d{2}):(\\d{2}):(\\d{2}),(\\d+) FunctionEdge\\s+-\\s+([^:]+):\\s+(.*)')

day_seconds = 24 * 60 * 60

# I need to build a map from 'filename' to 'sample identifier' (e.g. "NA12878"),
# so I load it from a two-column file.
def load_sample_keys(filename='1kgenomes_jobs.txt'):
    inf = open(filename, 'r')
    # assume the first line is a header.
    lines = [tuple(x.rstrip('\n').split('\t')) for x in inf.readlines()[1:]]
    inf.close()
    return dict([(job + '-logshort.txt', sample) for (job, sample) in lines])

class StepException(Exception):
    def __init__(self, found, line):
        self.found = found
        self.line = line
    def __repr__(self):
        return 'StepError(%s in %s)' % (self.found, self.line)

def find_steps(string):
    found = [step for step in steps if string.find(step) >= 0]
    if len(found) == 1: return found[0]
    if len(found) > 1: raise StepException(found, string)
    return None

class LogTime:
    def __init__(self, hrs, mins, secs, prev_logtime):
        self.hrs = hrs
        self.mins = mins
        self.secs = secs
        self.prev = prev_logtime
        # 'timestamp' is a number of seconds
        self.timestamp = hrs * 60 * 60 + mins * 60 + secs

        # calculate the difference in seconds relative to the previous log time
        if self.prev:
            self.diff = self.timestamp - self.prev.timestamp
        # otherwise, this is the first log time
        else:
            self.diff = self.timestamp

        # I use 'diff' to account for successive log lines where
        # the clock rolls over (midnight) in between the lines.
        if self.diff < 0:
            self.diff = (day_seconds - self.prev.timestamp) + self.timestamp
        if self.prev: self.timestamp = self.prev.timestamp + self.diff

    def __repr__(self):
        return '%02d:%02d:%02d %d' % (self.hrs, self.mins, self.secs, self.timestamp)

# to be clear, this parses a log file
def parse_file(filename):
    inf = open(filename, 'r')
    lineCount = 0
    prev_logtime = None
    logtimes = []

    # starts : STRING -> LogTime
    # ends : STRING -> LogTime
    #   where each STRING key identifies the particular sub-task whose
    #   start and end time is being tracked.  The difference between the
    #   timestamps of these two LogTime objects is the elapsed time of this
    #   subtask, and the total time of a step is the summed elapsed times of
    #   all subtasks which belong to that step.
    starts = {}
    ends = {}

    # total_times : STRING -> DOUBLE
    #    contains the total amount of time spent in each distinct step,
    #    summed over the length of this log file.
    total_times = {}
    # total_calls : STRING -> INT
    #    contains the total calls made to each distinct step
    total_calls = {}
    for step in steps: total_times[step] = 0.0
    total_calls = defaultdict(int)

    try:
        for line in [x.rstrip('\n') for x in inf.readlines()]:
            m = patt.match(line)
            lineCount += 1
            if m:  # It's a FunctionEdge line
                hours = int(m.group(1))
                mins = int(m.group(2))
                secs = int(m.group(3))
                edgeType = m.group(5)
                body = m.group(6)
                step = find_steps(body)
                logtime = LogTime(hours, mins, secs, prev_logtime)
                logtimes.append(logtime)
                # if step is truthy, then this is a FunctionEdge of
                # one of the pre-identified steps, above.
                if step:
                    if edgeType == 'Starting':
                        starts[body] = logtime
                    elif edgeType == 'Done':
                        ends[body] = logtime
                        if body in starts:
                            time = ends[body].timestamp - starts[body].timestamp
                            total_times[step] += time
                            total_calls[step] += 1
                prev_logtime = logtime
    finally:
        inf.close()

    # Average out times depending on number of calls
    for step in steps:
        if total_calls[step] != 0:
            logging.info(': '.join([step, str(total_times[step])]))
            total_times[step] /= total_calls[step]
    if len(logtimes) > 0:
        execution = 0.0
        for step in steps:
            execution += total_times[step]

        for step in steps:
            if total_times[step] != 0:
                frac = float(total_times[step]) / float(execution)
                logging.info('%.1f\t%.1f%%\t%s' % (total_times[step], 100.0 * frac, step))

    return total_times


def insert_run_phase_time(db, run_id, key, timing):
    c = db.cursor()
    key = key.lower()
    cursor = c.execute("SELECT id FROM perf_steps WHERE name=?", (key,))
    step_id_cursor = cursor.fetchone()
    if not step_id_cursor:
        c.execute("INSERT INTO perf_steps (name) VALUES (?)", (key,))
        cursor = c.execute("SELECT id FROM perf_steps WHERE name = ?", (key,))
        step_id = cursor.fetchone()[0]
    else:
        step_id = step_id_cursor[0]
    c.execute("INSERT INTO perf_measurements (stepid, run_id, step_time) VALUES (?, ?, ?)",
              (step_id, run_id, timing))
    db.commit()

# Pass the filenames of the logfiles you want to parse in on the command line.
# TODO(hammer): use optparse
# TODO(hammer): add some tests
def main(args):
    db_fn = args[-1]
    try:
        sampleCount = 0
        for arg in args[:-1]:
            run_id = report_metadata.report_metadata_to_db(arg, db_fn)
            t = parse_file(arg)
            sample = "Test"
            db = sqlite3.connect(db_fn)
            for key in list(t.keys()):
                if t[key] != 0:
                    logging.info('%s\t%s\t%d' % (sample, key.replace(' ', '_'), t[key]))
                    insert_run_phase_time(db, run_id, key.replace(' ', '_'), t[key])
            db.close()
            sampleCount += 1
    except StepException as e:
        logging.error(e.found)
        logging.error(e.line)

if __name__=="__main__":
    main(sys.argv[1:])
