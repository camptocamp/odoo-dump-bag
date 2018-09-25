# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import errno
import json
import logging
import os
import shutil
import subprocess
import tempfile

from contextlib import contextmanager
from subprocess import PIPE

from .exception import DumpNotExistError, DumpStorageError

_logger = logging.getLogger(__name__)


class StorageOptions():
    """ Base options for commanders """
    _commander = None


class StorageCommander():
    """ Base storage commander.

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

    def push_to_storage(self, dbname, source_path, filename):
        raise NotImplementedError

    @contextmanager
    def read_from_storage(self, dbname, filename):
        """ Get a file from storage for reading

        Context manager so it can clean the files after usage
        """
        raise NotImplementedError

    def list_by_db(self, dbname=None):
        """ Return a dict with files path/url

        :param dbname: name of a dbname to filter
        :return: dictionary {dbname: [list of files]}
        """
        raise NotImplementedError

    def read_dump(self, dbname, filename):
        with self.read_from_storage(dbname, filename) as f:
            for chunk in iter(lambda: f.read(1024), b''):
                yield chunk

    def download_commands(self, dbname, filename):
        return [], {}


class LocalStorageCommander(StorageCommander):
    """ Commander used for tests only.

    :params options: options for the commands
    :type options: LocalOptions

    """

    def push_to_storage(self, dbname, source_path, filename):
        source = os.path.join(source_path, filename)
        target_dir = os.path.join(self.options.storage_dir, dbname)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        target = os.path.join(target_dir, filename)
        shutil.copy2(source, target)

    @contextmanager
    def read_from_storage(self, dbname, filename):
        storage_dir = self.options.storage_dir
        fullpath = os.path.join(storage_dir, dbname, filename)
        if not os.path.exists(fullpath):
            raise DumpNotExistError('%s dump does not exist' % (filename,))
        with open(fullpath, 'rb') as f:
            yield f

    def list_by_db(self, dbname=None):
        files = {}
        storage_dir = self.options.storage_dir
        for (dirpath, __, filenames) in os.walk(storage_dir):
            directory = os.path.basename(dirpath)
            if dbname and dbname != directory:
                continue
            for filename in filenames:
                files.setdefault(directory, set())
                files[directory].add(filename)
        return files


class LocalOptions():
    """ Options for the local storage commander """
    _commander = LocalStorageCommander

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir


class S3StorageCommander(StorageCommander):
    """ Commander used for storing on S3

    :params options: options for the commands
    :type options: S3Options

    """

    def _env_variables(self):
        vars = {'AWS_ACCESS_KEY_ID': self.options.access_key,
                'AWS_SECRET_ACCESS_KEY': self.options.secret_access_key}
        return vars

    def _exec_s3_cmd(self, command):
        s3env = os.environ.copy()
        s3env.update(**self._env_variables())
        proc = subprocess.Popen(command, env=s3env, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode:
            _logger.error(
                'error when running aws command:\n%s', stderr.decode('utf8'),
            )
            raise DumpStorageError(stderr.decode('utf8'))
        return stdout, stderr

    def push_to_storage(self, dbname, source_path, filename):
        key = "%s/%s" % (dbname, filename)
        self._push_object(source_path, filename, key)
        self._add_expire_tag(key)
        _logger.info('pushed dump %s to S3', filename)

    def _push_object(self, source_path, filename, key):
        source = os.path.join(source_path, filename)
        target = "s3://%s/%s" % (self.options.bucket, key)
        command = ['aws', 's3', 'cp', source, target]
        self._exec_s3_cmd(command)

    def _add_expire_tag(self, key):
        """Add an Expire=True tag on the pushed object

        We set a tag so we can configure a rule on S3 to automatically remove
        the dumps after some time
        """
        tagging = "TagSet=[{Key=Expire,Value=True}]"
        command = ['aws', 's3api', 'put-object-tagging',
                   '--bucket', self.options.bucket,
                   '--key', key,
                   '--tagging', tagging,
                   ]
        self._exec_s3_cmd(command)

    @contextmanager
    def read_from_storage(self, dbname, filename):
        """ Get a file from storage for reading

        Context manager so it can clean the files after usage
        """
        source = "s3://%s/%s/%s" % (self.options.bucket, dbname, filename)
        _logger.info('Initiating download from S3 for %s', source)
        tmpdir = tempfile.mkdtemp()
        target = os.path.join(tmpdir, filename)
        command = ['aws', 's3', 'cp', source, target]
        self._exec_s3_cmd(command)
        try:
            with open(target, 'rb') as f:
                yield f
        finally:
            try:
                shutil.rmtree(tmpdir)
            except OSError as err:
                if err.errno != errno.ENOENT:  # file does not exist
                    raise

    def list_by_db(self, dbname=None):
        """ Return a dict with files path/url

        :param dbname: name of a dbname to filter
        :return: dictionary {dbname: [list of files]}
        """
        command = ['aws', 's3api', 'list-objects-v2',
                   '--bucket', self.options.bucket,
                   '--query', 'Contents[].Key']
        if dbname:
            command += ['--prefix', dbname + '/']
        stdout, _stderr = self._exec_s3_cmd(command)
        files = {}
        for line in json.loads(stdout.decode('utf8')) or []:
            spl = line.split('/')
            if len(spl) != 2:
                continue
            dbname, filename = spl
            files.setdefault(dbname, [])
            files[dbname].append(filename)
        return files

    def download_commands(self, dbname, filename):
        target = "s3://%s/%s/%s" % (self.options.bucket, dbname, filename)
        lines = [
            "# Using S3 (recommended if you have the access, see in lastpass)",
            "$$ aws --profile=odoo-dumps s3 cp $s3_url .",
        ]
        params = {
            's3_url': target,
        }
        return lines, params


class S3Options(StorageOptions):
    """ Options for the S3 Storage commander """
    _commander = S3StorageCommander

    def __init__(self, bucket, access_key, secret_access_key):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_access_key = secret_access_key
