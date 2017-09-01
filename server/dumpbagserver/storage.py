# Copyright 2017 Camptocamp SA
# License GPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
import shutil


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

    def get_from_storage(self, file_url):
        raise NotImplementedError

    def list_by_db(self):
        """ Return a dict with files path/url

        dictionary {dbname: [list of files]}
        """
        raise NotImplementedError


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

    def list_by_db(self):
        files = {}
        storage_dir = self.options.storage_dir
        for (dirpath, __, filenames) in os.walk(storage_dir):
            for filename in filenames:
                directory = os.path.basename(dirpath)
                files.setdefault(directory, [])
                files[directory] += filenames
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


class S3Options(StorageOptions):
    """ Options for the S3 Storage commander """
    _commander = LocalStorageCommander

    def __init__(self, bucket, access_key, secret_access_key, host=None):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_access_key = secret_access_key
        self.host = host
