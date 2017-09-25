# -*- coding: utf-8 -*-
from os import environ as env
from .database import StaticOptions, PostgresOptions
from .storage import LocalOptions, S3Options
from .encryption import NoOpEncryptionOptions, GPGKeysOptions

from .exception import DumpConfigurationError


class FlaskConfig(object):
    SECRET_KEY = env.get('FLASK_SECRET_KEY', '')
    DEBUG = env.get('FLASK_DEBUG', False)


class DumpBagConfig(object):
    """ Configuration """

    @property
    def only_databases(self):
        only = env.get('BAG_ONLY_DATABASE', '').strip()
        return only.split(',') if only else []

    @property
    def exclude_databases(self):
        exclude = env.get('BAG_EXCLUDE_DATABASE', '').strip()
        return exclude.split(',') if exclude else []

    @property
    def database_kind(self):
        return env.get('BAG_DB_KIND', 'static')

    @property
    def storage_kind(self):
        return env.get('BAG_STORAGE_KIND', 'local')

    @property
    def encryption_kind(self):
        return env.get('BAG_ENCRYPTION_KIND', 'none')

    def database_options(self):
        kind = self.database_kind
        if kind == 'static':
            return StaticOptions()
        elif kind == 'postgres':
            db_host = env.get('BAG_DB_HOST')
            db_port = str(env.get('BAG_DB_PORT', 5432))
            db_user = env.get('BAG_DB_USER')
            db_password = env.get('BAG_DB_PASSWORD', '')
            if not (db_host and db_user):
                raise DumpConfigurationError(
                    "For postgres, the following environment variables "
                    "are required: \n"
                    " - BAG_DB_HOST\n"
                    " - BAG_DB_USER\n"
                    " - BAG_DB_PASSWORD"
                )
            return PostgresOptions(db_host, db_user, db_password, port=db_port)
        else:
            raise DumpConfigurationError(
                "'%s' is not a valid kind of database among [static,postgres]"
                % (kind,)
            )

    def storage_options(self):
        kind = self.storage_kind
        if kind == 'local':
            storage_dir = env.get('BAG_STORAGE_LOCAL_DIR')
            if not storage_dir:
                raise DumpConfigurationError(
                    "For local storage, the following environment variables "
                    "are required: \n"
                    " - BAG_LOCAL_STORAGE_DIR\n"
                )
            return LocalOptions(storage_dir)
        elif kind == 's3':
            bucket = env.get('BAG_S3_BUCKET_NAME')
            access_key = env.get('BAG_S3_ACCESS_KEY')
            secret_access_key = env.get('BAG_S3_SECRET_ACCESS_KEY')
            if not (bucket and access_key and secret_access_key):
                raise DumpConfigurationError(
                    "For S3 storage, the following environment variables "
                    "are required: \n"
                    " - BAG_S3_BUCKET_NAME\n"
                    " - BAG_S3_ACCESS_KEY\n"
                    " - BAG_S3_SECRET_ACCESS_KEY"
                )
            return S3Options(bucket, access_key, secret_access_key)
        else:
            raise DumpConfigurationError(
                "'%s' is not a valid kind of storage among [local,s3]"
                % (kind,)
            )

    def encryption_options(self):
        kind = self.encryption_kind
        if kind == 'none':
            return NoOpEncryptionOptions()
        elif kind == 'gpg':
            recipients = env.get('BAG_GPG_RECIPIENTS', '')
            if not recipients:
                raise DumpConfigurationError(
                    "For GPG encryption, the following environment variables "
                    "are required: \n"
                    " - BAG_GPG_RECIPIENTS"
                )
            recipients = [r.strip() for r in recipients.split(',')]
            return GPGKeysOptions(recipients)
        else:
            raise DumpConfigurationError(
                "'%s' is not a valid kind of storage among [none,gpg]"
                % (kind,)
            )
