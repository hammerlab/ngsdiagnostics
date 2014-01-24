from django.db import models

# Create your models here.
class RunDescription(models.Model):
    timestamp = models.DateTimeField('Run timestamp')
    args = models.CharField(max_length=10000)

class PerfStep(models.Model):
    step_name = models.CharField(max_length=100)

class PerfMeasurement(models.Model):
    step = models.ForeignKey(PerfStep)
    perf_run = models.ForeignKey(RunDescription)
    step_time = models.IntegerField()

