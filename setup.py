from setuptools import setup

setup(
    name='ngsdiagnostics',
    version='0.1',
    long_description=__doc__,
    packages=['perfdash'],
    scripts=['scripts/run_perfdash.py', 'scripts/report_metadata.py'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['flask']
)
