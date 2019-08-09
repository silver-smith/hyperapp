from pathlib import Path
import os

from pony.orm import *

from hyperapp.common.module import Module


SQLITE_DB_PATH = Path('~/.local/share/hyperapp/server/db.sqlite').expanduser()

# base class for modules using ponyorm
class PonyOrmModule(Module):

    def __init__(self, name):
        super().__init__(name)
        self.db = this_module.db

    def make_entity(self, entity_name, primary_key=None, **fields):
        return self.make_inherited_entity(entity_name, self.db.Entity, primary_key, **fields)

    def make_inherited_entity(self, entity_name, base, primary_key=None, **fields):
        if primary_key:
            args = tuple(fields[key] for key in primary_key)
            PrimaryKey(*args)
            # PrimaryKey adds _indexes_ attribute to our frame, expects it in entity attributes
            fields['_indexes_'] = locals()['_indexes_']
        entity = type(entity_name, (base,), fields)
        return entity


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        sql_debug('SQL_DEBUG' in os.environ)
        SQLITE_DB_PATH.parent.mkdir(exist_ok=True)
        self.db = Database('sqlite', str(SQLITE_DB_PATH), create_db=True)

    def init_phase_3(self, services):
        self.db.generate_mapping(create_tables=True)
