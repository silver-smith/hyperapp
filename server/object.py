

MIN_ROWS_RETURNED = 10


class Column(object):

    def __init__( self, id, title=None, type='str' ):
        self.id = id
        self.title = title
        self.type = type

    def as_json( self ):
        return dict(
            id=self.id,
            title=self.title,
            type=self.type
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


class DictObject(object):

    def __init__( self ):
        self._d = {}

    def __setattr__( self, attr, value ):
        if attr == '_d':
            return object.__setattr__(self, attr, value)
        self._d[attr] = value

    def __setitem__( self, attr, value ):
        if attr == '_d':
            return object.__setattr__(self, attr, value)
        self._d[attr] = value

    def as_json( self ):
        return self._d


class Response(object):

    def __init__( self ):
        self.open = None
        self.result = DictObject()

    def as_json( self ):
        d = {}
        if self.open:
            d['open'] = self.open
        if self.result:
            d['result'] = self.result.as_json()
        return d


class Request(object):

    def __init__( self, params ):
        assert isinstance(params, dict), repr(params)
        self.params = params

    def __getattr__( self, name ):
        return self.params[name]

    def __getitem__( self, name ):
        return self.params[name]

    def make_response( self ):
        return Response()

    def make_response_open( self, obj ):
        response = self.make_response()
        response.open = obj.get()
        return response

    def make_response_result( self, **kw ):
        response = self.make_response()
        for name, value in kw.items():
            response.result[name] = value
        return response


class ObjectBase(object):

    def response( self, open=None ):
        if open is not None:
            assert isinstance(open, Object), repr(open)
            open_obj = open.get()
        else:
            open_obj = None
        return Response('open', obj=open_obj)

    def process_request( self, request ):
        method = request['method']
        if method == 'run_command':
            command_id = request['command_id']
            return self.run_command(request, command_id)
        else:
            assert False, repr(method)  # Unknown method

    def run_command( self, request, command_id ):
        assert False, repr(command_id)  # Unknown command


class Object(ObjectBase):

    def __init__( self, path ):
        self.path = path

    def get_path( self ):
        return self.path

    def get_commands( self ):
        return []

    def get( self, **kw ):
        return dict(
            iface_id=self.iface.id,
            view_id=self.view_id,
            path=self.get_path(),
            commands=[cmd.as_json() for cmd in self.get_commands()],
            **kw)

    def response( self, open=None ):
        if open is not None:
            assert isinstance(open, Object), repr(open)
            open_obj = open.get()
        else:
            open_obj = None
        return Response('open', obj=open_obj)

    def process_request( self, request ):
        method = request['method']
        if method == 'get':
            return request.make_response_result(object=self.get())
        else:
            return ObjectBase.process_request(self, request)


class ListObject(Object):

    def __init__( self, path ):
        Object.__init__(self, path)
        self.key_column_idx = self._pick_key_column_idx(self.get_columns())

    def _pick_key_column_idx( self, columns ):
        for idx, column in enumerate(self.get_columns()):
            if column.id == 'key':
                return idx
        assert False, 'Missing "key" column id'

    def get( self, **kw ):
        elements, has_more = self.get_elements_json()
        return Object.get(self,
            columns=[column.as_json() for column in self.get_columns()],
            elements=elements,
            has_more=has_more,
            **kw)

    def get_elements_json( self, count=None, key=None ):
        elements, has_more = self.get_elements(count, key)
        return ([elt.as_json() for elt in elements], has_more)

    def process_request( self, request ):
        method = request['method']
        if method == 'get_elements':
            key = request['key']
            count = request['count']
            elements, has_more = self.get_elements_json(count, key)
            return request.make_response_result(fetched_elements = dict(
                elements=elements,
                has_more=has_more))
            return response
        elif method == 'run_element_command':
            command_id = request['command_id']
            element_key = request['element_key']
            return self.run_element_command(request, command_id, element_key)
        else:
            return Object.process_request(self, request)

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
        to_idx = from_idx + max(count or 0, MIN_ROWS_RETURNED)
        has_more = to_idx <= len(elements)
        return (elements[from_idx:to_idx], has_more)

    def get_all_elements( self ):
        raise NotImplementedError(self.__class__)

    def run_element_command( self, request, command_id, element_key ):
        assert False, repr(command_id)  # Unexpected command_id
