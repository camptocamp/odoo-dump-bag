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
