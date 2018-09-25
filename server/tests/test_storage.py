import mock
import pytest
import os

from dumpbagserver import storage


@pytest.fixture
def local_options(tmpdir):
    options = storage.LocalOptions(tmpdir.strpath)
    return options


@pytest.fixture
def s3_options():
    options = storage.S3Options('foo', 'bar', 'baz')
    return options


@pytest.fixture
def local_commander(local_options):
    return storage.StorageCommander.new_commander(local_options)


@pytest.fixture
def s3_commander(s3_options):
    return storage.StorageCommander.new_commander(s3_options)


@pytest.fixture
def test_file(tmpdir):
    filename = 'test_file'
    path = tmpdir.join(filename).strpath
    with open(path, 'wb') as t:
        t.write(b'some content')
    return tmpdir.strpath, filename


def configure_mock_popen(mock_popen, attrs, returncode):
    process_mock = mock.Mock()
    process_mock.configure_mock(**attrs)
    mock_popen.return_value = process_mock
    process_mock.returncode = 0
    return mock_popen


def assert_s3_env_access(mock_popen, commander):
    __tracebackhide__ = True
    process_env = mock_popen.call_args[1]['env']

    if process_env['AWS_ACCESS_KEY_ID'] != commander.options.access_key:
        pytest.fail('AWS_ACCESS_KEY_ID is not in the S3 process environment')

    secret = commander.options.secret_access_key
    if process_env['AWS_SECRET_ACCESS_KEY'] != secret:
        pytest.fail('AWS_SECRET_ACCESS_KEY is not in '
                    'the S3 process environment')


def test_commander_factory(local_options, s3_options):
    cmd = storage.StorageCommander.new_commander(local_options)
    assert type(cmd) is storage.LocalStorageCommander
    cmd = storage.StorageCommander.new_commander(s3_options)
    assert type(cmd) is storage.S3StorageCommander
    with pytest.raises(TypeError):
        cmd = storage.StorageCommander.new_commander(
            storage.StorageOptions()
        )


def test_local_push(test_file, local_commander):
    tmpdir, filename = test_file
    source = os.path.join(tmpdir, filename)
    local_commander.push_to_storage('db1', tmpdir, filename)
    target = os.path.join(local_commander.options.storage_dir, 'db1', filename)
    assert os.path.exists(target)
    assert open(target).read() == open(source).read()


def test_local_read(tmpdir, local_commander):
    source = os.path.join(tmpdir.strpath, 'db1', 'test')
    os.makedirs(os.path.join(tmpdir.strpath, 'db1'))
    with open(source, 'wb') as f:
        f.write(b'line1\nline2\nline3')
    with local_commander.read_from_storage('db1', 'test') as content:
        # we read as bytes because we are dealing with dumps...
        assert content.read() == b'line1\nline2\nline3'


def _create_empty_files(tmpdir, local_commander):
    # create empty files so we can check if the tree is returned correctly
    for db in ('db1', 'db2', 'db3'):
        os.makedirs(os.path.join(tmpdir.strpath, db))
        for idx in range(3):
            source = os.path.join(tmpdir.strpath, db, 'dump%s.pg' % (idx,))
            with open(source, 'wb'):
                pass


def test_local_list_by_db(tmpdir, local_commander):
    _create_empty_files(tmpdir, local_commander)
    tree = local_commander.list_by_db()
    assert tree == {
        'db1': {'dump0.pg', 'dump1.pg', 'dump2.pg'},
        'db2': {'dump0.pg', 'dump1.pg', 'dump2.pg'},
        'db3': {'dump0.pg', 'dump1.pg', 'dump2.pg'},
    }


def test_local_list_by_db_filter(tmpdir, local_commander):
    _create_empty_files(tmpdir, local_commander)
    tree = local_commander.list_by_db(dbname='db2')
    assert tree == {
        'db2': {'dump0.pg', 'dump1.pg', 'dump2.pg'},
    }


@mock.patch('subprocess.Popen')
def test_s3_push(mock_popen, test_file, s3_commander):
    mock_popen = configure_mock_popen(
        mock_popen,
        {'communicate.return_value': (b'', b'')},
        0
    )

    tmpdir, filename = test_file
    s3_commander.push_to_storage('db1', tmpdir, filename)
    assert mock_popen.call_count == 2
    assert_s3_env_access(mock_popen, s3_commander)


@mock.patch('subprocess.Popen')
def test_s3_push_object(mock_popen, test_file, s3_commander):
    mock_popen = configure_mock_popen(
        mock_popen,
        {'communicate.return_value': (b'', b'')},
        0
    )

    tmpdir, filename = test_file
    source = os.path.join(tmpdir, filename)
    s3_commander._push_object(tmpdir, filename, 'db1/' + filename)
    assert mock_popen.call_count == 1
    url = 's3://%s/%s/%s' % (s3_commander.options.bucket, 'db1', filename)
    assert mock_popen.call_args[0] == ([
        'aws', 's3', 'cp', source, url
    ],)
    assert_s3_env_access(mock_popen, s3_commander)


@mock.patch('subprocess.Popen')
def test_s3_add_expire_tag(mock_popen, test_file, s3_commander):
    mock_popen = configure_mock_popen(
        mock_popen,
        {'communicate.return_value': (b'', b'')},
        0
    )

    s3_commander._add_expire_tag('db1/foo')
    assert mock_popen.call_count == 1
    expected_tag = "TagSet=[{Key=Expire,Value=True}]"
    assert mock_popen.call_args[0] == ([
        'aws', 's3api', 'put-object-tagging',
        '--bucket', s3_commander.options.bucket,
        '--key', 'db1/foo', '--tagging', expected_tag
    ],)
    assert_s3_env_access(mock_popen, s3_commander)


@mock.patch('subprocess.Popen')
@mock.patch('tempfile.mkdtemp')
def test_s3_read_from_storage(mock_mkdtemp, mock_popen, tmpdir, s3_commander):
    # force mkdtemp to use our test tmp directory so we can fake the
    # download of a file from S3
    mock_mkdtemp.return_value = tmpdir.strpath

    filename = 'test.pg'

    # tmpfile is the file copied by S3 in the directory created by mkdtemp
    # and is later read
    tmpfile = os.path.join(tmpdir.strpath, filename)

    def cp_file():
        with open(tmpfile, 'wb') as f:
            f.write(b'line1\nline2\nline3')
        return (b'', b'')

    process_mock = mock.Mock()
    mock_popen.return_value = process_mock
    process_mock.returncode = 0
    process_mock.communicate.side_effect = cp_file

    with s3_commander.read_from_storage('db1', filename) as f:
        assert f.read() == b'line1\nline2\nline3'

    url = 's3://%s/%s/%s' % (s3_commander.options.bucket, 'db1', filename)
    assert mock_popen.call_count == 1
    assert mock_popen.call_args[0] == ([
        'aws', 's3', 'cp', url, tmpfile
    ],)
    assert_s3_env_access(mock_popen, s3_commander)


@mock.patch('subprocess.Popen')
def test_s3_list_by_db(mock_popen, s3_commander):
    communicate_return = (
        # stdout
        b'['
        b'"README",'
        b'"db1/db1-20170904-092333.pg",'
        b'"db2/db1-20170904-094333.pg",'
        b'"db2/db1-20170904-094500.pg",'
        b'"db2/db2-20170904-110917.pg",'
        b'"db3/db3-20170904-110936.pg",'
        b'"db3/db3-20170904-120000.pg"'
        b']',
        # stderr
        b''
    )
    mock_popen = configure_mock_popen(
        mock_popen,
        {'communicate.return_value': communicate_return},
        0
    )

    dumps = s3_commander.list_by_db()
    assert dumps == {
        'db1': ['db1-20170904-092333.pg'],
        'db2': ['db1-20170904-094333.pg',
                'db1-20170904-094500.pg',
                'db2-20170904-110917.pg'],
        'db3': ['db3-20170904-110936.pg', 'db3-20170904-120000.pg']}

    assert mock_popen.call_count == 1
    assert mock_popen.call_args[0] == ([
        'aws', 's3api', 'list-objects-v2', '--bucket',
        s3_commander.options.bucket, '--query', 'Contents[].Key'
    ],)
    assert_s3_env_access(mock_popen, s3_commander)


@mock.patch('subprocess.Popen')
def test_s3_list_by_db_filter(mock_popen, s3_commander):
    communicate_return = (
        # stdout
        b'['
        b'"db2/db1-20170904-094333.pg",'
        b'"db2/db1-20170904-094500.pg",'
        b'"db2/db2-20170904-110917.pg"'
        b']',
        # stderr
        b''
    )
    mock_popen = configure_mock_popen(
        mock_popen,
        {'communicate.return_value': communicate_return},
        0
    )

    dumps = s3_commander.list_by_db(dbname='db2')
    assert dumps == {
        'db2': ['db1-20170904-094333.pg',
                'db1-20170904-094500.pg',
                'db2-20170904-110917.pg'],
        }

    assert mock_popen.call_count == 1
    assert mock_popen.call_args[0] == ([
        'aws', 's3api', 'list-objects-v2', '--bucket',
        s3_commander.options.bucket, '--query', 'Contents[].Key',
        '--prefix', 'db2/'
    ],)
    assert_s3_env_access(mock_popen, s3_commander)
