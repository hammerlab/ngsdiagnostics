from flask import Flask
from flask import render_template
import json
import StringIO
import csv

app = Flask(__name__)

@app.route('/perfdash/data')
def data():
    # Hardcoded data until I get the perf data DB model ported with Flask
    data = [['step','2013-09-11 14:34:30+00:00','2013-09-11 14:34:32+00:00','2013-09-11 14:34:36+00:00','2013-09-11 14:34:41+00:00','2013-09-13 10:13:03+00:00'],
     ['MergeSamFiles','17503','10020','11940','10961','3196'],
     ['wallclock','92100','58678','61922','86268','30997'],
     ['PrintReads','2433','1633','1773','1864','1680'],
     ['RealignerTargetCreator','771','577','711','605','551'],
     ['IndelRealigner','1035','628','621','620','445'],
     ['MarkDuplicates','19983','9165','8141','32254','3540'],
     ['BaseRecalibrator','1142','1485','986','103','1064'],
     ['SortSam','20286','15122','14641','14882','8370']]
    output = StringIO.StringIO()
    csv_writer = csv.writer(output, delimiter='	')
    for x in data:
        csv_writer.writerow(x)
    return output.getvalue()

@app.route('/')
def index():
    # Hardcoded data until I get the perf data ported from the Django store to the Flask store
    step_names = ["MergeSamFiles", "PrintReads", "MarkDuplicates", "SortSam", "wallclock", "IndelRealigner", "BaseRecalibrator", "RealignerTargetCreator"];
    return render_template('main.html', step_names_json=json.dumps(step_names), step_names=step_names)

if __name__ == '__main__':
    app.run(debug=True)
