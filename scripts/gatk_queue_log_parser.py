#!/usr/bin/python
import argparse
from  datetime import datetime as dt, time, timedelta as td
import hashlib
import logging
import re
import sqlite3
import sys
from collections import defaultdict

# NB: Whitespace-separated tokens are quoted in ISMMS logs, so 'bwa mem' won't work
# NB: bwa mem output is piped to SortSam in the ISMMS pipeline
BWA_STEPS = ['bwa mem']
GATK_STEPS = ['RealignerTargetCreator', 'IndelRealigner', 'BaseRecalibrator',
              'PrintReads', 'ReduceReads', 'UnifiedGenotyper', 'HaplotypeCaller']
PICARD_STEPS = ['SortSam', 'MergeSamFiles', 'MarkDuplicates', 'CalculateHsMetrics',
                'CollectGcBiasMetrics', 'CollectMultipleMetrics']
OTHER_STEPS = ['ContEst', 'VariantAnnotator', 'AnnotateCosegregation',
               'AnnotateLikelyPathogenic', 'VariantEval',
               'org.broadinstitute.sting.tools.CatVariants']
STEPS = BWA_STEPS + GATK_STEPS + PICARD_STEPS + OTHER_STEPS


#
# Extract
#
START_TIME_RE = re.compile('Date/Time: (\\d{4}/\\d{2}/\\d{2} \\d{2}:\\d{2}:\\d{2})')
def handle_start_time_line(match, run_info):
    start_time_string = match.group(1)
    start_time = dt.strptime(start_time_string, '%Y/%m/%d %H:%M:%S')
    run_info['start_time'] = start_time


ARGS_RE = re.compile('Program Args: (.*)$')
def handle_args_line(match, run_info):
    run_info['args'] = match.group(1)


# TODO(hammer): pick this up in a more general way
# TODO(hammer): handle if more than one distinct sample is found
SAMPLE_RE= re.compile("SM:([^\\\\]+)")
def handle_sample_line(match, run_info):
    run_info['sample'] = match.group(1)


FUNCTION_EDGE_RE = re.compile('INFO\\s+(\\d{2}):(\\d{2}):(\\d{2}),(\\d+) FunctionEdge\\s+-\\s+([^:]+):\\s+(.*)')
def handle_function_edge_line(match, run_info):
    h, m, s, ms, edge_type, body = match.groups()

    # TODO(hammer): handle runs > 24 hours
    line_t = time(int(h), int(m), int(s))
    start_dt = run_info.get('start_time')
    if not start_dt:
        raise Exception('Found a FunctionEdge line before start time could be determined.')
    line_d = start_dt.date() if line_t > start_dt.time() else start_dt.date() + td(days=1)
    line_dt = dt.combine(line_d, line_t)

    step = [step for step in STEPS if step in body]
    if len(step) == 0:
        return
    elif len(step) > 1:
        raise Exception('Matched multiple steps (%s) in %s' % (','.join(step), body))
    else:
        step = step[0]

    if edge_type in ('Starting', 'Done'):
        body_hash = hashlib.md5(body.encode()).hexdigest()
        # TODO(hammer): move to dict for step instance info?
        run_info['steps'][step].append([body_hash, edge_type, line_dt, body])


def parse_file(filename):
    run_info = {}
    run_info['steps'] = defaultdict(list)
    line_actions = [(START_TIME_RE, handle_start_time_line),
                    (ARGS_RE, handle_args_line),
                    (SAMPLE_RE, handle_sample_line),
                    (FUNCTION_EDGE_RE, handle_function_edge_line)]

    with open(filename, 'r') as infile:
        for line in infile:
            for action_re, action_handler in line_actions:
                match = action_re.search(line)
                if match: action_handler(match, run_info)

    return run_info


#
# Transform
#

# TODO(hammer): do this in the database (ELT!)
def get_avg_step_times(run_info):
    avg_times = {}
    for step_name, step_info in run_info['steps'].items():
        ss = sorted(step_info)
        # TODO(hammer): add some error checking to this very cute comprehension
        step_times = [(x[2] - y[2]).seconds for (x, y) in zip(ss[::2], ss[1::2])]
        logging.info("Step times for step %s: %s" % (step_name, step_times))
        avg_times[step_name] = sum(step_times) / len(step_times)
    return avg_times


def make_dict_of_lists(list_of_pairs):
    d = defaultdict(list)
    for (key, value) in list_of_pairs: d[key].append(value)
    return d


def parse_gatk_command_line(body):
    clean_body = [token.strip("'") for token in body.strip().split()]
    java_index = clean_body.index('java')
    gatk_index = clean_body.index('org.broadinstitute.sting.gatk.CommandLineGATK')
    java_args = clean_body[java_index + 1:gatk_index]
    gatk_args = clean_body[gatk_index + 1:]
    gatk_args_list_of_pairs = [(param_name.strip('-'), param_value)
                               for (param_name, param_value)
                               in zip(gatk_args[::2], gatk_args[1::2])]
    gatk_args_dict = make_dict_of_lists(gatk_args_list_of_pairs)
    return [java_args, gatk_args_dict]


# run_info positional arguments after this function:
# (0: body_hash, 1: edge_type, 2: line_dt, 3: body, 4: java_args, 5: gatk_args)
def get_gatk_command_line_args(run_info):
    for step_name, step_info in run_info['steps'].items():
        if step_name in GATK_STEPS:
          new_step_info = [info + parse_gatk_command_line(info[3]) for info in step_info]
          run_info['steps'][step_name] = new_step_info


#
# Load
#

# TODO(hammer): generalize to handle sqlite3 and psycopg2
def get_conn(db):
    return sqlite3.connect(db)


# TODO(hammer): make consistent with get_step_id
def get_run_id(conn, run_info):
    c = conn.cursor()
    # NB datetime.timestamp() is only in Python >= 3.3
    timestamp = int(run_info['start_time'].timestamp())
    args = run_info['args']
    sample = run_info['sample']
    try:
        result = c.execute("""\
        INSERT INTO run_timing_metadata (run_timestamp, run_args, sample)
        VALUES      (?, ?, ?)""", (timestamp, args, sample))
        run_id = result.lastrowid
        conn.commit()
        logging.info('Inserted run id %s into run_timing_metadata: (%s, %s, %s)'
                     % (run_id, timestamp, args, sample))
    except sqlite3.IntegrityError as err:
        logging.info("Run metadata (args, timestamp, sample) already existed")

    result = c.execute("""\
    SELECT rowid from run_timing_metadata
    WHERE  run_timestamp = ? and run_args = ? and sample = ?
    """, (timestamp, args, sample))
    row_id = result.fetchone()[0]
    return row_id


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
        result = c.execute("INSERT INTO perf_steps (name) VALUES (?)", (step_name,))
        step_id = result.lastrowid
        conn.commit()
        logging.info('Inserted step id %s into perf_steps: (%s)' % (step_id, step_name))
    return step_id


def insert_step_time(conn, run_id, step_name, step_time, run_info):
    step_id = get_step_id(conn, step_name)
    step_info = run_info['steps'][step_name]
    c = conn.cursor()
    # TODO(hammer): match beginning and end times
    for s in step_info:
        if s[1] == 'Done': continue
        if step_name in GATK_STEPS:
            c.execute("INSERT INTO perf_measurements \
                       (stepid, run_id, step_time, start_time, input_files, \
                        output_files, reference_file, step_hash, step_body) \
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (step_id, run_id, step_time, int(s[2].timestamp()),
                       ','.join(s[5]['I']), ','.join(s[5]['o']), ','.join(s[5]['R']),
                       s[0], s[3]))
            conn.commit()
            logging.info('Inserted new row into perf_measurements: \
                          (%s, %s, %s, %s, %s, %s, %s, %s, %s)' %
                         (step_id, run_id, step_time, int(s[2].timestamp()),
                          ','.join(s[5]['I']), ','.join(s[5]['o']), ','.join(s[5]['R']),
                          s[0], s[3]))
        else:
            c.execute("INSERT INTO perf_measurements \
                       (stepid, run_id, step_time) \
                       VALUES (?, ?, ?)",
                      (step_id, run_id, step_time))
            conn.commit()
            logging.info('Inserted new row into perf_measurements: (%s, %s, %s)' %
                         (step_id, run_id, step_time))


def store_results(db, run_info, avg_step_times):
    conn = get_conn(db)
    run_id = get_run_id(conn, run_info)
    for step_name, avg_step_time in avg_step_times.items():
      step_id = get_step_id(conn, step_name)
      insert_step_time(conn, run_id, step_name, avg_step_time, run_info)


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
    store_in_db = True if args.db else False

    for logfile in args.logfiles:
        # Extract
        run_info = parse_file(logfile)
        logging.info('Run info parsed from %s' % logfile)

        # Transform
        get_gatk_command_line_args(run_info)
        avg_step_times = get_avg_step_times(run_info)
        logging.info('Average step times: %s' % (avg_step_times))

        # Load
        if store_in_db: store_results(args.db, run_info, avg_step_times)


if __name__ == '__main__':
    main(sys.argv)
