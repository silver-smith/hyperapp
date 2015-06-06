from common.util import path2str
from common.interface.interface import iface_registry
from common.json_decoder import JsonDecoder
from util import WeakValueMultiDict
from common.interface import Interface


MIN_ROWS_RETURNED = 10


class Subscription(object):

    def __init__( self ):
        self.path2client = WeakValueMultiDict()  # path -> client

    def add( self, path, client ):
        self.path2client.add(path2str(path), client)

    def remove( self, path, client ):
        self.path2client.remove(path2str(path), client)

    def distribute_update( self, path, diff ):
        assert isinstance(diff, Diff), repr(diff)
        for client in self.path2client.get(path2str(path)):
            client.send_update(path, diff)


subscription = Subscription()


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
            key=self.key,
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


class Diff(object):
    pass


class ListDiff(Diff):

    @classmethod
    def add_one( cls, key, element ):
        return cls(key, key, [element])

    @classmethod
    def delete( cls, key ):
        return cls(key, key, [])

    def __init__( self, start_key, end_key, elements ):
        self.start_key = start_key  # replace elements from this one
        self.end_key = end_key      # up to (and including) this one
        self.elements = elements    # with these elemenents

    def as_json( self ):
        return dict(
            start_key=self.start_key,
            end_key=self.end_key,
            elements=[elt.as_json() for elt in self.elements])


class Notification(object):

    def __init__( self ):
        self.updates = []  # (path, ListDiff) list

    def add_update( self, path, diff ):
        self.updates.append((path, diff))

    def as_json( self ):
        d = dict()
        if self.updates:
            d['updates'] = [(path, diff.as_json()) for path, diff in self.updates]
        return d


class Response(Notification):

    def __init__( self, request_id, result_dict=None ):
        Notification.__init__(self)
        self.request_id = request_id
        self.object = None
        self.result_dict = result_dict

    def as_json( self ):
        d = Notification.as_json(self)
        d['request_id'] = self.request_id
        if self.object:
            d['object'] = self.object
        if self.result_dict:
            d['result'] = self.result_dict
        return d


class Request(object):

    def __init__( self, client, iface, data ):
        assert isinstance(iface, Interface), repr(iface)
        assert isinstance(data, dict), repr(data)
        self.client = client
        self.iface = iface
        self.path = data['path']
        self.command_id = data['command']
        self.request_id = data.get('request_id')
        params_type = self.iface.get_command_params_type(self.command_id)
        decoder = JsonDecoder(iface_registry)
        self.params = decoder.decode(params_type, data)

    # request_id is included only in requests, not notifications
    def is_response_needed( self ):
        return self.request_id is not None

    def make_response( self, result_dict=None ):
        return Response(self.request_id, result_dict)

    def make_response_object( self, obj ):
        result = obj.get()
        self.iface.validate_result(self.command_id, result)
        return self.make_response(result)

    def make_response_result( self, **kw ):
        self.iface.validate_result(self.command_id, kw)
        return self.make_response(kw)

    def make_response_update( self, path, diff ):
        assert isinstance(diff, ListDiff), repr(diff)
        response = self.make_response()
        response.add_update(path, diff)
        return response


class Object(object):

    def __init__( self, path ):
        self.path = path

    def get_path( self ):
        return self.path

    def get_commands( self ):
        return []

    def get( self ):
        return dict(
            iface_id=self.iface.iface_id,
            proxy_id=self.proxy_id,
            view_id=self.view_id,
            path=self.get_path(),
            contents=self.get_contents(),
            )

    def get_contents( self, **kw ):
        return dict(
            commands=[cmd.as_json() for cmd in self.get_commands()],
            **kw)

    def process_request( self, request ):
        command_id = request.command_id
        if command_id == 'get':
            return self.process_request_get(request)
        if command_id == 'subscribe':
            return self.process_request_subscribe(request)
        elif command_id == 'subscribe':
            self.subscribe(request)
        elif command_id == 'unsubscribe':
            self.unsubscribe(request)
        else:
            assert False, repr(command_id)  # Unknown command

    def process_request_get( self, request ):
        self.subscribe(request)
        return request.make_response_result(**self.get())

    def process_request_subscribe( self, request ):
        self.subscribe(request)
        return request.make_response_result(**self.get_contents())

    def subscribe( self, request ):
        subscription.add(self.path, request.client)

    def unsubscribe( self, request ):
        subscription.remove(self.path, request.client)


class ListObject(Object):

    def __init__( self, path ):
        Object.__init__(self, path)
        self.key_column_idx = self._pick_key_column_idx(self.get_columns())

    def _pick_key_column_idx( self, columns ):
        for idx, column in enumerate(self.get_columns()):
            if column.id == 'key':
                return idx
        assert False, 'Missing "key" column id'

    def get_contents( self, **kw ):
        elements, has_more = self.get_elements_json()
        return Object.get_contents(self,
            columns=[column.as_json() for column in self.get_columns()],
            elements=elements,
            has_more=has_more,
            selected_key=None,
            **kw)

    def get_elements_json( self, count=None, key=None ):
        elements, has_more = self.get_elements(count, key)
        return ([elt.as_json() for elt in elements], has_more)

    def process_request( self, request ):
        if request.command_id == 'get_elements':
            key = request.params.key
            count = request.params.count
            elements, has_more = self.get_elements_json(count, key)
            return request.make_response_result(fetched_elements=dict(
                elements=elements,
                has_more=has_more))
            return response
        elif request.command_id == 'run_element_command':
            command_id = request.command_id
            element_key = request.params.element_key
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


# return list object (base) with selected_key selected
class ListObjectElement(Object):

    def __init__( self, base, selected_key ):
        assert isinstance(base, ListObject), repr(base)
        self._base = base
        self._selected_key = selected_key

    def get( self ):
        return dict(
            iface_id=self._base.iface.iface_id,
            proxy_id=self._base.proxy_id,
            view_id=self._base.view_id,
            path=self._base.get_path(),
            contents=self.get_contents(),
            )

    def get_contents( self, **kw ):
        return self._base.get_contents(
            selected_key=self._selected_key,
            **kw)
