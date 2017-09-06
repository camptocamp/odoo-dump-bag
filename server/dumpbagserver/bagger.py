import errno
import shutil
import tempfile
import time

from contextlib import contextmanager
from string import Template

from flask import url_for

from .database import DatabaseCommander, Database
from .storage import StorageCommander
from .encryption import EncryptionCommander


class Bagger():

    def __init__(self, config):
        self.config = config
        db_commander = DatabaseCommander.new_commander(
            self.config.database_options()
        )
        self.db = Database(db_commander, exclude=self.config.exclude_databases)
        self.storage = StorageCommander.new_commander(
            self.config.storage_options()
        )
        self.encrypter = EncryptionCommander.new_commander(
            self.config.encryption_options()
        )

    def list_databases(self):
        return self.db.list_databases()

    def has_dump_for_today(self, dbname):
        dumps = self.storage.list_by_db().get(dbname, [])
        start = '%s-%s' % (dbname, time.strftime("%Y%m%d"))
        return any(filename.startswith(start) for filename in dumps)

    @contextmanager
    def temporary_working_dir(self):
        tmpdir = tempfile.mkdtemp()
        try:
            yield tmpdir
        finally:
            try:
                shutil.rmtree(tmpdir)
            except OSError as err:
                if err.errno != errno.ENOENT:  # dir does not exist
                    raise

    def bag_one_database(self, dbname):
        with self.temporary_working_dir() as tmpdir:
            filename = self.db.create_dump_file(tmpdir, dbname)
            filename = self.encrypter.encrypt(tmpdir, filename)
            self.storage.push_to_storage(dbname, tmpdir, filename)
        return filename

    def bag_all_databases(self):
        for dbname in self.list_databases():
            self.bag_one_database(dbname)

    def list_dumps(self):
        return self.storage.list_by_db()

    def read_dump(self, db, filename):
        return self.storage.read_dump(db, filename)

    def public_keys(self):
        return self.encrypter.public_keys()

    def download_commands(self, dbname, dump):

        lines = [
            "# Using wget",
            "$$ wget $url",
        ]
        params = {
            'dbname': dbname,
            'filename': dump,
            'url': url_for(
                'download_dump',
                db=dbname,
                filename=dump,
                _external=True,
            ),
        }
        storage_command, storage_params = self.storage.download_commands(
            dbname, dump
        )
        if storage_command:
            lines.append('')
            lines += storage_command
        if storage_params:
            params.update(storage_params)

        encrypter_dl_func = self.encrypter.download_commands
        (encryption_command,
            encryption_params) = encrypter_dl_func(dbname, dump)

        if encryption_command:
            lines.append('')
            lines += encryption_command
        if encryption_params:
            params.update(encryption_params)

        tmpl = Template('\n'.join(lines))
        s = tmpl.substitute(**params)
        return s
