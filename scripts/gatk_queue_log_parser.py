#!/usr/bin/python
import argparse
import datetime
import hashlib
import logging
import re
import sqlite3
import sys
from collections import defaultdict

# NB: Whitespace-separated tokens are quoted in ISMMS logs, so 'bwa mem' won't work
# NB: bwa mem output is piped to SortSam in the ISMMS pipeline
STEPS = ['bwa mem', 'SortSam', 'RealignerTargetCreator', 'IndelRealigner',
         'MergeSamFiles', 'MarkDuplicates', 'BaseRecalibrator', 'PrintReads',
         'CalculateHsMetrics', 'CollectGcBiasMetrics', 'CollectMultipleMetrics',
         'ReduceReads', 'ContEst', 'UnifiedGenotyper', 'HaplotypeCaller',
         'VariantAnnotator', 'AnnotateCosegregation', 'AnnotateLikelyPathogenic',
         'VariantEval', 'org.broadinstitute.sting.tools.CatVariants']


#
# Extract
#
START_TIME_RE= re.compile('Date/Time: (\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2})')
def handle_start_time_line(match, run_info):
    start_time_string = match.group(1)
    start_time = datetime.datetime.strptime(start_time_string, '%Y/%m/%d %H:%M:%S')
    run_info['start_time'] = start_time


ARGS_RE= re.compile('Program Args: (.*)$')
def handle_args_line(match, run_info):
    run_info['args'] = match.group(1)


FUNCTION_EDGE_RE = re.compile('INFO\\s+(\\d{2}):(\\d{2}):(\\d{2}),(\\d+) FunctionEdge\\s+-\\s+([^:]+):\\s+(.*)')
def handle_function_edge_line(match, run_info):
    h, m, s, ms, edge_type, body = match.groups()

    step = [step for step in STEPS if step in body]
    if len(step) == 0:
        return
    elif len(step) > 1:
        raise Exception("Matched multiple steps (%s) in %s" % (','.join(step), body))
    else:
        step = step[0]

    if edge_type in ('Starting', 'Done'):
        body_hash = hashlib.md5(body.encode()).hexdigest()
        run_info['steps'][step].append((body_hash, edge_type, ':'.join([h, m, s])))


def parse_file(filename):
    run_info = {}
    run_info['steps'] = defaultdict(list)
    line_actions = [(START_TIME_RE, handle_start_time_line),
                    (ARGS_RE, handle_args_line),
                    (FUNCTION_EDGE_RE, handle_function_edge_line)]

    with open(filename, 'r') as infile:
        for line in infile:
            for action_re, action_handler in line_actions:
                match = action_re.search(line)
                if match: action_handler(match, run_info)

    return run_info


#
# Load
#

# TODO(hammer): generalize to handle sqlite3 and psycopg2
def get_conn(db):
    return sqlite3.connect(db)


def get_step_id(conn, step_name):
    # For a known step_name, look up its step_id
    # For a new step_name, create a new step_id
    c = conn.cursor()
    step_name = step_name.lower()
    result = c.execute("SELECT id FROM perf_steps WHERE name=?", (step_name,))
    known_step_id = result.fetchone()
    if known_step_id:
        step_id = known_step_id[0]
    else:
        # NB: some databases will make us commit() this INSERT
        result = c.execute("INSERT INTO perf_steps (name) VALUES (?)", (step_name,))
        step_id = result.lastrowid
    return step_id


def insert_step_time(conn, run_id, step_name, step_time):
    step_id = get_step_id(conn, step_name)
    c = conn.cursor()
    c.execute("INSERT INTO perf_measurements (stepid, run_id, step_time) VALUES (?, ?, ?)",
              (step_id, run_id, step_time))
    conn.commit()


#
# Main
#
def main(argv):
    parser = argparse.ArgumentParser(description='Process GATK-Queue log files.')
    parser.add_argument('--logfiles', nargs='+', help='one or more GATK-Queue log files')
    parser.add_argument('--db', nargs='?', help='sqlite database')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose: logging.basicConfig(level=logging.DEBUG)
    persist_to_db = True if args.db else False

    for logfile in args.logfiles:
        run_info = parse_file(logfile)
        logging.info('Run info parsed from %s: %s' % (logfile, run_info))


if __name__ == '__main__':
    main(sys.argv)
