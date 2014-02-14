from django.db import models

# Create your models here.
class RunDescription(models.Model):
    timestamp = models.DateTimeField('Run timestamp')
    args = models.CharField(max_length=10000)

    def __str__(self):
        return str(self.timestamp) + ":" + self.args

class PerfStep(models.Model):
    step_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.step_name

class PerfMeasurement(models.Model):
    step = models.ForeignKey(PerfStep)
    perf_run = models.ForeignKey(RunDescription)
    step_time = models.IntegerField()

    def __str__(self):
        return self.step.step_name + ":" + str(self.step_time) + "@" + str(self.perf_run.timestamp)
