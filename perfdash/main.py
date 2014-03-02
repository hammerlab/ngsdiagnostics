from flask import request, g, render_template

import json
import sqlite3
import os
import datetime

from perfdash import app


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['PERF_DB_FILE'])
    rv.row_factory = sqlite3.Row
    return rv

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.route('/perfdash/data')
def data():
    query = """\
SELECT name, step_time, run_timestamp
FROM   perf_steps, perf_measurements, run_timing_metadata
WHERE  perf_measurements.stepid = perf_steps.id AND
       perf_measurements.run_id = run_timing_metadata.rowid
"""
    db = get_db()
    cur = db.execute(query)
    rows = cur.fetchall()
    # This is probably really slow.  We need to convert the rows into
    # a list of lists, where inner list has the phase name as the
    # first element and the measurements as the remainder.  We iterate
    # through the result set and store the measurement into a
    # dictionary of dictionaries.  The outer dictionary key is
    # phase_name, and its lookup results in a dictionary who's key is
    # timestamp and value is the perf measurement.
    # TODO(nealsid): Read the database section from
    # https://leanpub.com/D3-Tips-and-Tricks, as there is probably a
    # much easier way to issue SQL queries that can transform the data
    # into something that d3 can use.
    data_dict = {}
    # We need to keep track of all the timestamps
    timestamps = set()
    for x in rows:
        # Each element in rows is a tuple of 3 elements, and the first
        # is the phase name
        phase_name = x[0]
        if phase_name not in data_dict:
            data_dict[phase_name] = {}
        timestamp = x[2]
        measurement = x[1]
        timestamps.add(timestamp)
        data_dict[phase_name][timestamp] = measurement

    header_list = ['step']
    sorted_timestamps = sorted(timestamps)
    header_list.extend([datetime.datetime.fromtimestamp(x).__str__()
                        for x in sorted_timestamps])
    data = []
    data.append(header_list)
    for phase in data_dict:
        one_phase_data = []
        one_phase_data.append(phase)
        for timestamp in sorted_timestamps:
            if timestamp in data_dict[phase]:
                one_phase_data.append(data_dict[phase][timestamp])
            else:
                one_phase_data.append('')
        data.append(one_phase_data)
    # TODO (nealsid): Move the step filtering into the query itself.
    requested_steps = request.args.get('requested_steps')
    new_data = data
    if requested_steps:
        new_data = [data[0]]
        requested_steps = [x.lower() for x in requested_steps.split(",")]
        app.logger.debug("requested steps: %s", requested_steps)
        new_data.extend([step_data for step_data in data[1:]
                         if step_data[0].lower() in requested_steps])
    app.logger.debug("new data: %s", str(new_data))
    app.logger.debug("Returning data for following steps: %s",
                     ",".join([x[0] for x in new_data]))
    return '\n'.join(['\t'.join([str(x) for x in row]) for row in new_data])

@app.route('/')
def index():
    # TODO (nealsid): Query step names from database.
    step_names = ["MergeSamFiles", "PrintReads", "MarkDuplicates", "SortSam",
                  "wallclock", "IndelRealigner", "BaseRecalibrator",
                  "RealignerTargetCreator"];
    return render_template('main.html',
                           step_names_json=json.dumps(step_names),
                           step_names=step_names)

if __name__ == '__main__':
    app.run(debug=True)

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
