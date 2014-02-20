from flask import Flask
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    PERF_DB_FILE=os.path.join(app.root_path, 'perf-runs.db'),
    DEBUG=True,
    # TODO (nealsid): change this
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))

import perfdash.main
