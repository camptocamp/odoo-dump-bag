# -*- coding: utf-8 -*-
from os import environ as env
from .database import StaticOptions, PostgresOptions
from .storage import LocalOptions, S3Options

from .exception import DumpConfigurationError


class FlaskConfig(object):
    SECRET_KEY = env.get('FLASK_SECRET_KEY', '')
    DEBUG = env.get('FLASK_DEBUG', False)


class DumpBagConfig(object):
    """ Configuration """

    exclude_databases = env.get('BAG_EXCLUDE_DATABASE', '').split(',')

    def database_options(self):
        kind = env.get('BAG_DB_KIND', 'static')
        if kind == 'static':
            return StaticOptions()
        elif kind == 'postgres':
            db_host = env.get('BAG_DB_HOST')
            db_port = env.get('BAG_DB_PORT', 5432)
            db_user = env.get('BAG_DB_USER')
            db_password = env.get('BAG_DB_PASSWORD')
            if not (db_host and db_user and db_password):
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
        kind = env.get('BAG_STORAGE_KIND', 'local')
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
            bucket = env.get('BAG_S3_BUCKET')
            access_key = env.get('BAG_S3_ACCESS_KEY')
            secret_access_key = env.get('BAG_S3_SECRET_ACCESS_KEY')
            host = env.get('BAG_S3_HOST')
            if not (bucket and access_key and secret_access_key):
                raise DumpConfigurationError(
                    "For S3 storage, the following environment variables "
                    "are required: \n"
                    " - BAG_S3_BUCKET\n"
                    " - BAG_S3_ACCESS_KEY\n"
                    " - BAG_S3_SECRET_ACCESS_KEY"
                )
            return S3Options(bucket, access_key, secret_access_key, host=host)
        else:
            raise DumpConfigurationError(
                "'%s' is not a valid kind of storage among [local,s3]"
                % (kind,)
            )
