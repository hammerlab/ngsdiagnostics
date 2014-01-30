from django.shortcuts import render
from django.http import HttpResponse
from perfdash.models import RunDescription, PerfMeasurement, PerfStep
import datetime
import csv
import StringIO
import json

def data_as_tsv(request):
    measurements = PerfMeasurement.objects.all()

    # A dictionary of step name => dictionary of date to measurement
    step_numbers = {}
    all_dates = set()
    for p in measurements:
        step_name = p.step.step_name
        measurement_date = p.perf_run.timestamp
        all_dates.add(measurement_date)
        if step_numbers.has_key(step_name) and step_numbers[step_name].has_key(measurement_date):
            continue
        if not step_numbers.has_key(step_name):
            step_numbers[step_name] = {}
        step_numbers[step_name][measurement_date] = p.step_time
    
    columns = ["step"]
    for a in sorted(all_dates):
        columns.append(str(a))
    
    output = StringIO.StringIO()
    csv_writer = csv.writer(output, delimiter='	')
    csv_writer.writerow(columns)

    for step_name in step_numbers:
        one_row = []
        one_row.append(step_name)
        for a in sorted(all_dates):
            if step_numbers[step_name].has_key(a):
                one_row.append(step_numbers[step_name][a])
            else:
                one_row.append(-1)
        csv_writer.writerow(one_row)
    return HttpResponse(output.getvalue())


    # for p in measurements:
    #     vals = [str(p.perf_run.timestamp), str(p.perf_run.id), p.step.step_name, str(p.step_time)]
    #     vals = [p.step.step_name, p.perf_run.timestamp, str(p.step_time)]
    #     csv_writer.writerow(vals)

#     return HttpResponse(output.getvalue())

def index(request):
    step_names = [x.step_name for x in PerfStep.objects.all()]
    return render(request, 'perfdash/main.html', {'step_names_json':json.dumps(step_names), 'step_names':step_names})

