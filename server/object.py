from iface import ListIface


MIN_ROWS_RETURNED = 10


class Column(object):

    def __init__( self, id, title=None ):
        self.id = id
        self.title = title

    def as_json( self ):
        return dict(
            id=self.id,
            title=self.title,
            )


class Element(object):

    def __init__( self, key, row, commands=None ):
        self.key = key
        self.row = row  # value list
        self.commands = commands or []

    def as_json( self ):
        return dict(
            row=self.row,
            commands=[cmd.as_json() for cmd in self.commands],
            )


class Command(object):

    def __init__( self, id, text, desc, shortcut=None ):
        self.id = id
        self.text = text
        self.desc = desc
        self.shortcut = shortcut

    def as_json( self ):
        return dict(
            id=self.id,
            text=self.text,
            desc=self.desc,
            shortcut=self.shortcut,
            )


class Object(object):

    def __init__( self, path ):
        self.path = path


class ListObject(Object):

    iface = ListIface()

    def __init__( self, path ):
        Object.__init__(self, path)
        self.key_column_idx = self._pick_key_column_idx(self.get_columns())

    def _pick_key_column_idx( self, columns ):
        for idx, column in enumerate(self.get_columns()):
            if column.id == 'key':
                return idx
        assert False, 'Missing "key" column id'

    def get_columns( self ):
        return self.columns

    def get_elements( self, count=None, from_key=None ):
        elements = self.get_all_elements()
        from_idx = 0
        if from_key is not None:
            for idx, elt in enumerate(elements):
                if elt.row[self.key_column_idx] == from_key:
                    from_idx = idx + 1
                    break
            else:
                print 'Warning: unknown "from_key" is requested: %r' % from_key
        return elements[from_idx:from_idx + max(count or 0, MIN_ROWS_RETURNED)]

    def get_all_elements( self ):
        raise NotImplementedError(self.__class__)
