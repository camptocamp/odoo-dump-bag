from os import environ as env

import pytest

from dumpbagserver import config, exception, database


def test_database_options_static():
    env['BAG_DB_KIND'] = 'static'
    conf = config.DumpBagConfig()
    assert type(conf.database_options()) == database.StaticOptions


def test_database_options_postgres_missing_conf():
    env['BAG_DB_KIND'] = 'postgres'
    conf = config.DumpBagConfig()
    with pytest.raises(exception.DumpConfigurationError):
        conf.database_options()

    env['BAG_DB_HOST'] = 'postgres'
    env['BAG_DB_USER'] = 'postgres'
    env['BAG_DB_PASSWORD'] = 'postgres'
    assert type(conf.database_options()) == database.PostgresOptions


def test_database_options_wrong_kind():
    env['BAG_DB_KIND'] = 'foo'
    conf = config.DumpBagConfig()
    with pytest.raises(exception.DumpConfigurationError):
        conf.database_options()
