from flask import Flask
import os

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
  PERF_DB_FILE=os.path.join(app.root_path, 'data/perf-runs.db'),
  DEBUG=True
))
print(os.path.join(app.root_path, 'data/perf-runs.db'))


import perfdash.main
