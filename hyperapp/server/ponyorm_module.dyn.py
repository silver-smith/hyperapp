from pathlib import Path
import os

from pony.orm import *

from .module import ServerModule


SQLITE_DB_PATH = Path('~/.local/share/hyperapp/server/db.sqlite').expanduser()
MODULE_NAME = 'ponyorm'


# base class for modules using ponyorm
class PonyOrmModule(ServerModule):

    def __init__(self, name):
        super().__init__(name)
        self.db = this_module.db

    def make_entity(self, entity_name, **fields):
        return self.make_inherited_entity(entity_name, self.db.Entity, **fields)

    def make_inherited_entity(self, entity_name, base, **fields):
        return type(entity_name, (base,), fields)


class ThisModule(ServerModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        sql_debug('SQL_DEBUG' in os.environ)
        SQLITE_DB_PATH.parent.mkdir(exist_ok=True)
        self.db = Database('sqlite', str(SQLITE_DB_PATH), create_db=True)

    def init_phase3(self, services):
        self.db.generate_mapping(create_tables=True)
