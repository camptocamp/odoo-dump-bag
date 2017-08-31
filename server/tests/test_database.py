import pytest

from dumpbagserver import database, exception


@pytest.fixture
def static_options():
    options = database.StaticOptions()
    return options


@pytest.fixture
def commander(static_options):
    return database.DatabaseCommander.new_commander(static_options)


@pytest.fixture
def db(commander):
    return database.Database(commander)


@pytest.fixture
def db_with_exclude(commander):
    return database.Database(
        commander, exclude=['postgres', 'template0', 'template1']
    )


def test_commander_factory(static_options):
    cmd = database.DatabaseCommander.new_commander(
        static_options
    )
    assert type(cmd) is database.StaticDatabaseCommander
    cmd = database.DatabaseCommander.new_commander(
        database.PostgresOptions('foo', 'bar', 'baz')
    )
    assert type(cmd) is database.PostgresDatabaseCommander
    with pytest.raises(TypeError):
        cmd = database.DatabaseCommander.new_commander(
            database.DatabaseOptions()
        )


def test_list_database(db):
    dbs = db.list_databases()
    assert dbs == ['db1', 'db2', 'db3', 'postgres', 'template0', 'template1']


def test_list_database_exclude(db_with_exclude):
    db_with_exclude.exclude = ['postgres', 'template0', 'template1']
    dbs = db_with_exclude.list_databases()
    assert dbs == ['db1', 'db2', 'db3']


def test_dump_db_not_exist(db_with_exclude):
    with pytest.raises(exception.DumpingError):
        db_with_exclude.create_dump_file('template0', '/tmp/template0.pg')


def test_dump(db_with_exclude):
    db_with_exclude.create_dump_file('db1', '/tmp/template0.pg')
