# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import errno
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time

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

    def list_by_db(self):
        """ Return a dict with files path/url

        dictionary {dbname: [list of files]}
        """
        raise NotImplementedError

    def read_dump(self, dbname, filename):
        with self.read_from_storage(dbname, filename) as f:
            for chunk in iter(lambda: f.read(1024), b''):
                yield chunk

    def download_commands(self, dbname, filename):
        return [], {}

    def has_dump_for_today(self, dbname):
        dumps = self.list_by_db().get(dbname, [])
        start = '%s-%s' % (dbname, time.strftime("%Y%m%d"))
        return any(filename.startswith(start) for filename in dumps)


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

    def list_by_db(self):
        files = {}
        storage_dir = self.options.storage_dir
        for (dirpath, __, filenames) in os.walk(storage_dir):
            for filename in filenames:
                directory = os.path.basename(dirpath)
                files.setdefault(directory, [])
                files[directory].append(filename)
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
        source = os.path.join(source_path, filename)
        target = "s3://%s/%s/%s" % (self.options.bucket, dbname, filename)
        command = ['aws', 's3', 'cp', source, target]
        self._exec_s3_cmd(command)
        _logger.info('pushed dump %s to S3', filename)

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

    def list_by_db(self):
        """ Return a dict with files path/url

        dictionary {dbname: [list of files]}
        """
        command = ['aws', 's3api', 'list-objects-v2',
                   '--bucket', self.options.bucket,
                   '--query', 'Contents[].Key']
        stdout, _stderr = self._exec_s3_cmd(command)
        files = {}
        for line in json.loads(stdout.decode('utf8')):
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
