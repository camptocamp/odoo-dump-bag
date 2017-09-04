from string import Template

from .database import DatabaseCommander, Database
from .storage import StorageCommander


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

    def list_databases(self):
        return self.db.list_databases()

    def bag_one_database(self, dbname):
        with self.db.create_temporary_dump_file(dbname) as (path, filename):
            # TODO: encrypt
            self.storage.push_to_storage(dbname, path, filename)
        return filename

    def list_dumps(self):
        return self.storage.list_by_db()

    def read_dump(self, db, filename):
        return self.storage.read_dump(db, filename)

    def download_commands(self, dbname, dump):
        lines = [
            "# Using wget",
            "$$ wget $base_url/download/$dbname/$dump",
        ]
        params = {
            'base_url': self.config.base_url,
            'dbname': dbname,
            'dump': dump,
        }
        storage_command, storage_params = self.storage.download_commands(
            dbname, dump
        )
        if storage_command:
            lines.append('')
            lines += storage_command
        if storage_params:
            params.update(storage_params)

        tmpl = Template('\n'.join(lines))
        s = tmpl.substitute(**params)
        return s
