from os import environ as env

import pytest

from dumpbagserver import config, exception, database, storage, encryption


def test_database_options_static():
    env['BAG_DB_KIND'] = 'static'
    conf = config.DumpBagConfig()
    assert type(conf.database_options()) == database.StaticOptions


def test_database_options_postgres():
    env['BAG_DB_KIND'] = 'postgres'
    conf = config.DumpBagConfig()

    env.pop('BAG_DB_HOST', None)
    env.pop('BAG_DB_PORT', None)
    env.pop('BAG_DB_USER', None)
    env.pop('BAG_DB_PASSWORD', None)
    with pytest.raises(exception.DumpConfigurationError):
        conf.database_options()

    env['BAG_DB_HOST'] = 'postgres'
    env['BAG_DB_USER'] = 'postgres'
    env['BAG_DB_PASSWORD'] = 'postgres'
    options = conf.database_options()
    assert type(options) == database.PostgresOptions
    assert options.host == 'postgres'
    assert options.port == '5432'
    assert options.user == 'postgres'
    assert options.password == 'postgres'


def test_database_options_wrong_kind():
    env['BAG_DB_KIND'] = 'foo'
    conf = config.DumpBagConfig()
    with pytest.raises(exception.DumpConfigurationError):
        conf.database_options()


def test_storage_options_local():
    env['BAG_STORAGE_KIND'] = 'local'
    conf = config.DumpBagConfig()

    env.pop('BAG_STORAGE_LOCAL_DIR', None)
    with pytest.raises(exception.DumpConfigurationError):
        conf.storage_options()

    env['BAG_STORAGE_LOCAL_DIR'] = 'foo'
    options = conf.storage_options()
    assert type(options) == storage.LocalOptions
    assert options.storage_dir == 'foo'


def test_storage_options_s3():
    env['BAG_STORAGE_KIND'] = 's3'
    conf = config.DumpBagConfig()

    env.pop('BAG_S3_BUCKET_NAME', None)
    env.pop('BAG_S3_ACCESS_KEY', None)
    env.pop('BAG_S3_SECRET_ACCESS_KEY', None)
    with pytest.raises(exception.DumpConfigurationError):
        conf.storage_options()

    env['BAG_S3_BUCKET_NAME'] = 'foo'
    env['BAG_S3_ACCESS_KEY'] = 'bar'
    env['BAG_S3_SECRET_ACCESS_KEY'] = 'baz'
    options = conf.storage_options()
    assert type(options) == storage.S3Options
    assert options.bucket == 'foo'
    assert options.access_key == 'bar'
    assert options.secret_access_key == 'baz'


def test_storage_options_wrong_kind():
    env['BAG_STORAGE_KIND'] = 'foo'
    conf = config.DumpBagConfig()
    with pytest.raises(exception.DumpConfigurationError):
        conf.storage_options()


def test_encryption_options_none():
    env['BAG_ENCRYPTION_KIND'] = 'none'
    conf = config.DumpBagConfig()
    assert type(conf.encryption_options()) == encryption.NoOpEncryptionOptions


def test_encryption_options_gpg():
    env['BAG_ENCRYPTION_KIND'] = 'gpg'
    conf = config.DumpBagConfig()

    env.pop('BAG_GPG_RECIPIENTS', None)
    with pytest.raises(exception.DumpConfigurationError):
        conf.encryption_options()

    env['BAG_GPG_RECIPIENTS'] = 'someone@example.com'
    options = conf.encryption_options()
    assert type(options) == encryption.GPGKeysOptions
    assert options.recipients == ['someone@example.com']


def test_encryption_options_wrong_kind():
    env['BAG_ENCRYPTION_KIND'] = 'foo'
    conf = config.DumpBagConfig()
    with pytest.raises(exception.DumpConfigurationError):
        conf.encryption_options()
