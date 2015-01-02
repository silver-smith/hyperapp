
class Column(object):

    def __init__( self, idx, id, title ):
        self.idx = idx
        self.id = id
        self.title = title

    @classmethod
    def from_json( cls, idx, data ):
        return cls(idx, data['id'], data['title'])


class Command(object):

    def __init__( self, id, text, desc ):
        self.id = id
        self.text = text
        self.desc = desc

    @classmethod
    def from_json(cls, data ):
        return cls(data['id'], data['text'], data['desc'])


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

    def load_elements( self, load_count ):
        last_key = self.elements[-1].row[self.key_column_idx]
        self.connection.send(dict(method='get_elements',
                            key=last_key,
                            count=load_count))
        response = self.connection.receive()
        self.elements += [Element.from_json(elt) for elt in response['elements']]

    def element_command( self, command_id, element_key ):
        self.connection.send(dict(
            method='element_command',
            command_id=command_id,
            element_key=element_key))
        response = self.connection.receive()
        path = response['path']
        return ListObj(self.connection, response)

    def dir_commands( self ):
        return []

    def _find_key_column( self, columns ):
        for idx, col in enumerate(columns):
            if col.id == 'key':
                return col.idx
        assert False, 'No "key" column'
