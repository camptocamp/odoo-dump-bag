# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .exception import DumpingError


class DatabaseOptions():
    """ Base options for commanders """
    _commander = None


class DatabaseCommander():

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

    def exec_dump(self):
        raise NotImplementedError


class StaticDatabaseCommander(DatabaseCommander):
    """ Commander used for tests

    :params options: options for the commands
    :type options: DatabaseOptions

    """

    def list_databases(self, exclude=None):
        return ['db1', 'db2', 'db3', 'postgres', 'template0', 'template1']

    def exec_dump(self):
        return


class StaticOptions():
    """ Options for the static commander """
    _commander = StaticDatabaseCommander


class PostgresDatabaseCommander(DatabaseCommander):
    """ Commander used for PostgreSQL

    :params options: options for the commands
    :type options: PostgresOptions

    """

    def list_databases(self, exclude=None):
        return ['db1', 'db2', 'db3', 'postgres', 'template0', 'template1']

    def exec_dump(self):
        # pg_dump --format=c -h localhost -p 5555 -U late_tree_4086 late_tree_4086 -O --file rensales-prod.pg
        pass


class PostgresOptions(DatabaseOptions):
    """ Options for the PostgreSQL commander """
    _commander = PostgresDatabaseCommander

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password


class Database():

    def __init__(self, commander, exclude=None):
        self.exclude = exclude
        self.commander = commander

    def list_databases(self):
        databases = self.commander.list_databases()
        if self.exclude:
            databases = [db for db in databases
                         if db not in self.exclude]
        return databases

    def create_dump_file(self, dbname, target):
        databases = self.list_databases()
        if dbname not in databases:
            raise DumpingError('Database %s does not exist or is excluded'
                               % (dbname,))
        self.commander.exec_dump()
