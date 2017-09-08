from datetime import datetime, timedelta

import mock
import pytest

import dumpbagserver


@pytest.fixture
def bagger():
    config = mock.Mock(name='config')
    db = mock.Mock(name='db')
    storage = mock.Mock(name='storage')
    encryption = mock.Mock(name='encryption')

    config.exclude_databases = []
    config.database_options.return_value = db
    config.storage_options.return_value = storage
    config.encryption_options.return_value = encryption

    return dumpbagserver.bagger.Bagger(config)


def test_has_dump_for_today(bagger):
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d-%H%M%S')
    today = datetime.now().strftime('%Y%m%d-%H%M%S')
    bagger.storage.list_by_db.return_value = {}
    assert not bagger.has_dump_for_today('db1')
    bagger.storage.list_by_db.return_value = {
        'db1': ['db1-%s.pg.gpg' % yesterday],
        'db2': ['db2-%s.pg.gpg' % yesterday]
    }
    assert not bagger.has_dump_for_today('db1')
    bagger.storage.list_by_db.return_value = {
        'db1': ['db1-%s.pg.gpg' % today],
        'db2': ['db2-%s.pg.gpg' % yesterday]
    }
    assert bagger.has_dump_for_today('db1')
