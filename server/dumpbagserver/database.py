# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import os
import subprocess
import time

from subprocess import PIPE

from .exception import DumpingError


_logger = logging.getLogger(__name__)


class DatabaseOptions():
    """ Base options for commanders """
    _commander = None


class DatabaseCommander():
    """ Base commander.

    :meth:`new_commander` is a factory method that returns an instance
    of the commander determined by the type of the options.

    """

    def __init__(self, options):
        self.options = options

    @classmethod
    def new_commander(cls, options):
        klass = options._commander
        if not klass:
            raise TypeError('No commander class set for these options')
        return klass(options)

    def list_databases(self):
        raise NotImplementedError

    def exec_dump(self, dbname, target):
        raise NotImplementedError


class StaticDatabaseCommander(DatabaseCommander):
    """ Commander used for tests

    :params options: options for the commands
    :type options: StaticOptions

    """

    def list_databases(self):
        return ['db1', 'db2', 'db3', 'postgres', 'template0', 'template1']

    def exec_dump(self, dbname, target):
        with open(target, 'w') as fh:
            fh.write('test %s' % (dbname,))


class StaticOptions():
    """ Options for the static commander """
    _commander = StaticDatabaseCommander


class PostgresDatabaseCommander(DatabaseCommander):
    """ Commander used for PostgreSQL

    :params options: options for the commands
    :type options: PostgresOptions

    """

    def _env_variables(self):
        vars = {'PGPASSWORD': self.options.password,
                }
        return vars

    def list_databases(self):
        psql_env = os.environ.copy()
        psql_env.update(**self._env_variables())
        command = [
            'psql',
            '--host', self.options.host,
            '--port', str(self.options.port),
            '--username', self.options.user,
            '--quiet', '--no-align', '--tuples-only',
            '--dbname', 'postgres',
            '--command', 'SELECT datname FROM pg_database',
        ]
        proc = subprocess.Popen(
            command, env=psql_env, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        stdout, stderr = proc.communicate()
        if proc.returncode:
            _logger.error(
                'error when listing databases:\n%s', stderr.decode('utf8')
            )
        return stdout.decode('utf8').split()

    def exec_dump(self, dbname, target):
        psql_env = os.environ.copy()
        psql_env.update(**self._env_variables())
        command = [
            'pg_dump',
            '--format', 'c',
            '--host', self.options.host,
            '--port', self.options.port,
            '--username', self.options.user,
            '--no-owner',
            '--file', target,
            dbname
        ]
        proc = subprocess.Popen(
            command, env=psql_env, stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        stdout, stderr = proc.communicate()
        if proc.returncode:
            _logger.error(
                'error when creating dump:\n%s', stderr.decode('utf8')
            )
            raise DumpingError(stderr.decode('utf8'))


class PostgresOptions(DatabaseOptions):
    """ Options for the PostgreSQL commander """
    _commander = PostgresDatabaseCommander

    def __init__(self, host, user, password, port='5432'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password


class Database():

    def __init__(self, commander, only=None, exclude=None):
        self.only = only
        self.exclude = exclude
        self.commander = commander

    def list_databases(self):
        databases = self.commander.list_databases()
        if self.only:
            databases = [db for db in databases if db in self.only]
        if self.exclude:
            databases = [db for db in databases if db not in self.exclude]
        return databases

    def _generate_dump_name(self, dbname):
        now = time.strftime("%Y%m%d-%H%M%S")
        return '%s-%s.pg' % (dbname, now)

    def create_dump_file(self, tmpdir, dbname):
        databases = self.list_databases()
        if dbname not in databases:
            raise DumpingError('Database %s does not exist or is excluded'
                               % (dbname,))
        name = self._generate_dump_name(dbname)
        target = os.path.join(tmpdir, name)
        self.commander.exec_dump(dbname, target)
        return name
