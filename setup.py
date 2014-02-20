from setuptools import setup

setup(
    name='perfdash',
    version='0.1',
    long_description=__doc__,
    packages=['web/perfdash'],
    scripts=['scripts/run_perfdash.py', 'scripts/parser.py', 'scripts/report_metadata.py'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['flask']
)
