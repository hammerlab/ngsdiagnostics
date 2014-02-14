from flask import Flask, request, g, render_template

import csv
import json
import sqlite3
import StringIO
import os
import datetime

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    PERF_DB_FILE=os.path.join(app.root_path, 'perf-runs.db'),
    DEBUG=True,
    # TODO (nealsid): change this
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))

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
    query = "select name, step_time, run_timestamp from perf_steps, perf_measurements, run_timing_metadata where perf_measurements.stepid = perf_steps.id and perf_measurements.run_id = run_timing_metadata.rowid"
    db = get_db()
    cur = db.execute(query)
    rows = cur.fetchall()
    # This is probably really slow.  We need to convert the rows into
    # a list of lists, where inner list has the phase name as the
    # first element and the measurements as the remainder.
    data_dict = {}
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
    header_list.extend([datetime.datetime.fromtimestamp(x).__str__() for x in sorted_timestamps])
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
    # Hardcoded data until I get the perf data DB model ported with Flask
    # data = [['step','2013-09-11 14:34:30+00:00','2013-09-11 14:34:32+00:00','2013-09-11 14:34:36+00:00','2013-09-11 14:34:41+00:00','2013-09-13 10:13:03+00:00'],
    #  ['MergeSamFiles','17503','10020','11940','10961','3196'],
    #  ['wallclock','92100','58678','61922','86268','30997'],
    #  ['PrintReads','2433','1633','1773','1864','1680'],
    #  ['RealignerTargetCreator','771','577','711','605','551'],
    #  ['IndelRealigner','1035','628','621','620','445'],
    #  ['MarkDuplicates','19983','9165','8141','32254','3540'],
    #  ['BaseRecalibrator','1142','1485','986','103','1064'],
    #  ['SortSam','20286','15122','14641','14882','8370']]
    requested_steps = request.args.get('requested_steps')
    new_data = data
    if requested_steps:
        new_data = [data[0]]
        requested_steps = [x.lower() for x in requested_steps.split(",")]
        app.logger.debug("requested steps: %s", requested_steps)
        new_data.extend(filter(lambda step_data: step_data[0].lower() in requested_steps, data[1:]))
    app.logger.debug("new data: %s", str(new_data))
    app.logger.debug("Returning data for following steps: %s", ",".join([x[0] for x in new_data]))
    output = StringIO.StringIO()
    csv_writer = csv.writer(output, delimiter='	')
    for x in new_data:
        csv_writer.writerow(x)
    return output.getvalue()

@app.route('/')
def index():
    # Hardcoded data until I get the perf data ported from the Django store to the Flask store
    step_names = ["MergeSamFiles", "PrintReads", "MarkDuplicates", "SortSam", "wallclock", "IndelRealigner", "BaseRecalibrator", "RealignerTargetCreator"];
    return render_template('main.html', step_names_json=json.dumps(step_names), step_names=step_names)

if __name__ == '__main__':
    app.run(debug=True)


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
