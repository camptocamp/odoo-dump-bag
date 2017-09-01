import mock
import pytest
import os

from dumpbagserver import database, exception


@pytest.fixture
def static_options():
    options = database.StaticOptions()
    return options


@pytest.fixture
def postgres_options():
    options = database.PostgresOptions('foo', 'bar', 'baz')
    return options


@pytest.fixture
def commander(static_options):
    return database.DatabaseCommander.new_commander(static_options)


@pytest.fixture
def postgres_commander(postgres_options):
    return database.PostgresDatabaseCommander(postgres_options)


@pytest.fixture
def db(commander):
    return database.Database(commander)


@pytest.fixture
def db_with_exclude(commander):
    return database.Database(
        commander, exclude=['postgres', 'template0', 'template1']
    )


def test_commander_factory(static_options, postgres_options):
    cmd = database.DatabaseCommander.new_commander(
        static_options
    )
    assert type(cmd) is database.StaticDatabaseCommander
    cmd = database.DatabaseCommander.new_commander(
        postgres_options
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
        with db_with_exclude.create_temporary_dump_file('template0'):
            pass


def test_dump(db_with_exclude):
    with db_with_exclude.create_temporary_dump_file('db1') as dump:
        assert os.path.exists(dump)
        # file has been written (hardcoded for tests)
        assert open(dump, 'r').read() == 'test db1'


@mock.patch('subprocess.Popen')
def test_postgres_list_database(mock_popen, postgres_commander):
    process_mock = mock.Mock()
    command_stdout = (
        "template1\n"
        "template0\n"
        "postgres\n"
        "odoo\n"
        "odoodb\n"
        "prod\n"
        "prod_template\n"
    )
    attrs = {'communicate.return_value': (command_stdout, '')}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock
    dbs = postgres_commander.list_databases()
    assert dbs == ["template1", "template0", "postgres", "odoo", "odoodb",
                   "prod", "prod_template"]


@mock.patch('subprocess.Popen')
def test_postgres_exec_dump(mock_popen, postgres_commander):
    process_mock = mock.Mock()
    attrs = {'communicate.return_value': ('ok', '')}
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock
    postgres_commander.exec_dump('db1', '/tmp/test')
    assert mock_popen.called
