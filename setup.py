from setuptools import setup
import sys

if sys.version_info < (3, 3):
    print('Please upgrade to Python 3.3 or above.')
    sys.exit(1)

setup(
    name='ngsdiagnostics',
    version='0.1',
    long_description=__doc__,
    packages=['perfdash'],
    scripts=['scripts/run_perfdash.py',
             'scripts/gatk_queue_log_parser.py'],
    data_files=[('data', ['data/perf-runs.db'])],
    include_package_data=True,
    zip_safe=False,
    install_requires=['flask']
)
