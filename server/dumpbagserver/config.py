# -*- coding: utf-8 -*-
from os import environ as env


class FlaskConfig(object):
    SECRET_KEY = env.get('FLASK_SECRET_KEY', '')
    DEBUG = env.get('FLASK_DEBUG', False)


class DumpBagConfig(object):
    """ Configuration """

    # base_url = env['BASE_URL']

    # main_container = env.get('ODOO_CONTAINER', 'odoo')
