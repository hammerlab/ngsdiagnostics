ngsdiagnostics
==============

Diagnostic Scripts for an NGS Pipeline

To run inside of a venv (preferred):
```
$ curl -O 'https://gist.github.com/vsajip/4673395/raw/3420d9150ce1e9797dc8522fce7386d8643b02a1/pyvenvex.py'
$ python3 pyvenvex.py venv-ngsdiagnostics
$ cd venv-ngsdiagnostics
$ source bin/activate
$ git clone https://github.com/hammerlab/ngsdiagnostics.git
$ cd ngsdiagnostics
$ python setup.py install
$ run_perfdash.py
```

You should now be able to navigate to http://127.0.0.1:5000 and view the dashboard running with some [sample data](https://git.mssm.edu/hammerlab/ngsdiagnostics/blob/master/data/perf-runs.db).
