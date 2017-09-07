import mock
import pytest
import os

from dumpbagserver import encryption


@pytest.fixture
def noop_options(tmpdir):
    options = encryption.NoOpEncryptionOptions()
    return options


@pytest.fixture
def gpg_options():
    options = encryption.GPGKeysOptions(
        ['someone@example.com', 'another@example.com']
    )
    return options


@pytest.fixture
def noop_commander(noop_options):
    return encryption.EncryptionCommander.new_commander(noop_options)


@pytest.fixture
def gpg_commander(gpg_options):
    return encryption.EncryptionCommander.new_commander(gpg_options)


@pytest.fixture
def test_file(tmpdir):
    filename = 'test_file'
    path = tmpdir.join(filename).strpath
    with open(path, 'wb') as t:
        t.write(b'some content')
    return tmpdir.strpath, filename


def test_commander_factory(noop_options, gpg_options):
    cmd = encryption.EncryptionCommander.new_commander(noop_options)
    assert type(cmd) is encryption.NoOpEncryptionCommander
    cmd = encryption.EncryptionCommander.new_commander(gpg_options)
    assert type(cmd) is encryption.GPGKeysCommander
    with pytest.raises(TypeError):
        cmd = encryption.EncryptionCommander.new_commander(
            encryption.EncryptionOptions()
        )


def test_noop_encrypt(test_file, noop_commander):
    tmpdir, filename = test_file
    source = os.path.join(tmpdir, filename)
    content = open(source, 'rb').read()
    new_filename = noop_commander.encrypt(tmpdir, filename)

    target = os.path.join(tmpdir, new_filename)
    new_content = open(target, 'rb').read()
    # no encryption, should not have changed
    assert filename == new_filename
    assert content == new_content


def test_noop_public_keys(noop_commander):
    assert noop_commander.public_keys() == []


def test_noop_recipients(noop_commander):
    assert noop_commander.recipients() == []


def test_gpg_recipients(gpg_commander):
    assert gpg_commander.recipients() == gpg_commander.options.recipients


@mock.patch('subprocess.Popen')
def test_gpg_public_keys(mock_popen, gpg_commander):
    keys = (
        '-----BEGIN PGP PUBLIC KEY BLOCK-----\n'
        'Version: GnuPG v1\n'
        '\n'
        'mQMuBExgG+4RCACFGdLu8JNrLdZY8ZXyHZ0dqAul/FUaIAKuN2BNs9iv14X0cwUV\n'
        '6JAEAAIAAAAUAAAB/JIBAAoAAAABAAACEJICAAUAAAABAAACGJIEAAoAAAABAAAC\n'
        '-----END PGP PUBLIC KEY BLOCK-----\n'
    )
    process_mock = mock.Mock()
    process_mock.communicate.return_value = (
        # stdout
        keys.encode('utf8'),
        # stderr
        b''
    )
    mock_popen.return_value = process_mock
    process_mock.returncode = 0

    public_keys = gpg_commander.public_keys()
    # as we have 2 recipients but the popen mock returns 2 times
    # the same key, the test assume we should receive 2 times the same key
    # in real world, each recipient will have the same key
    assert public_keys == [keys, keys]
    assert mock_popen.call_count == 2
    # the list of recipients is defined in gpg_options()
    assert mock_popen.call_args_list[0][0] == ([
        'gpg', '--export', '-a', 'someone@example.com',
    ],)
    assert mock_popen.call_args_list[1][0] == ([
        'gpg', '--export', '-a', 'another@example.com',
    ],)


@mock.patch('subprocess.Popen')
def test_gpg_encrypt(mock_popen, test_file, gpg_commander):
    tmpdir, filename = test_file
    # gpg adds .gpg at the end of the encrypted file
    target_filename = filename + '.gpg'
    target = os.path.join(tmpdir, target_filename)

    def gpg_encrypt_content():
        with open(target, 'wb') as f:
            f.write(b'this is my encrypted content')
        return (b'', b'')

    process_mock = mock.Mock()
    process_mock.communicate.side_effect = gpg_encrypt_content
    mock_popen.return_value = process_mock
    process_mock.returncode = 0

    new_filename = gpg_commander.encrypt(tmpdir, filename)
    new_content = open(target, 'rb').read()
    # no encryption, should not have changed
    assert new_filename == target_filename
    assert new_content == b'this is my encrypted content'
