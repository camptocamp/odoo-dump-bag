# -*- coding: utf-8 -*-
from os import environ as env


class FlaskConfig(object):
    SECRET_KEY = env.get('FLASK_SECRET_KEY', '')
    DEBUG = env.get('FLASK_DEBUG', False)


class DumpBagConfig(object):
    """ Configuration """

    # base_url = env['BASE_URL']

    exclude_databases = env.get('BAG_EXCLUDE_DATABASE', [])
