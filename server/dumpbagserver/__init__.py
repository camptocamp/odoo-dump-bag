import logging

from flask import Flask
from . import config

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
root.addHandler(handler)

app = Flask(__name__)
app.config.from_object(config.FlaskConfig)
app_config = config.DumpBagConfig()

# views have to be imported after the application object is created.
import dumpbagserver.views  # noqa
