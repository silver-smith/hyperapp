from PySide import QtCore, QtGui
from util import make_action
import view_registry


class Column(object):

    def __init__( self, idx, id, title ):
        self.idx = idx
        self.id = id
        self.title = title

    @classmethod
    def from_json( cls, idx, data ):
        return cls(idx, data['id'], data['title'])


class Command(object):

    def __init__( self, id, text, desc, shortcut ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut
        self.enabled = True
        self.multi_select = False
        self.args = None

    @classmethod
    def from_json(cls, data ):
        return cls(data['id'], data['text'], data['desc'], data['shortcut'])

    def title( self ):
        return self.text

    def is_bound2inst( self ):
        return True

    def require_explicit_elt_arg( self ):
        return True

    def run_dir_command( self, obj, view ):
        print 'list_obj.Command.run_dir_command', obj, view
        new_obj = obj.run_dir_command(self.id)
        if not new_obj: return
        handle_ctr = view_registry.resolve_view('list')  # hardcoded for now
        view.open(handle_ctr(new_obj))

    def run_element_command( self, obj, view, element_key ):
        print 'list_obj.Command.run_element_command', obj, view
        new_obj = obj.run_element_command(self.id, element_key)
        if not new_obj: return
        handle_ctr = view_registry.resolve_view('list')  # hardcoded for now
        view.open(handle_ctr(new_obj))

    def make_dir_action( self, widget, obj, view ):
        return make_action(widget, self.text, self.shortcut, self.run_dir_command, obj, view)

    def make_element_action( self, widget, obj, view, element_key ):
        return make_action(widget, self.text, self.shortcut, self.run_element_command, obj, view, element_key)


class Element(object):

    def __init__( self, row, commands ):
        self.row = row
        self.commands = commands

    @classmethod
    def from_json( cls, data ):
        return cls(data['row'], [Command.from_json(cmd) for cmd in data['commands']])


class ListObj(object):

    def __init__( self, connection, response ):
        self.connection = connection
        self.path = response['path']
        self.dir_commands = [Command.from_json(cmd) for cmd in response['dir_commands']]
        self.columns = [Column.from_json(idx, column) for idx, column in enumerate(response['columns'])]
        self.elements = [Element.from_json(elt) for elt in response['elements']]
        self.key_column_idx = self._find_key_column(self.columns)

    def title( self ):
        return 'list obj'

    def element_count( self ):
        return len(self.elements)

    def ensure_element_count( self, element_count ):
        if element_count < self.element_count(): return
        self.load_elements(element_count - self.element_count())

    def element_idx2key( self, idx ):
        return self.elements[idx].row[self.key_column_idx]

    def element2key( self, elt ):
        return elt.row[self.key_column_idx]

    def load_elements( self, load_count ):
        last_key = self.element_idx2key(-1)
        self.connection.send(dict(method='get_elements',
                                  path=self.path,
                                  key=last_key,
                                  count=load_count))
        response = self.connection.receive()
        self.elements += [Element.from_json(elt) for elt in response['elements']]

    def run_element_command( self, command_id, element_key ):
        self.connection.send(dict(
            method='element_command',
            path=self.path,
            command_id=command_id,
            element_key=element_key,
            ))
        response = self.connection.receive()
        return ListObj(self.connection, response)

    def run_dir_command( self, command_id ):
        self.connection.send(dict(
            method='dir_command',
            path=self.path,
            command_id=command_id,
            ))
        response = self.connection.receive()
        return ListObj(self.connection, response)

    def get_dir_commands( self ):
        return self.dir_commands

    def _find_key_column( self, columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'
