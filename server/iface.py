from object import Object


class Iface(object):

    def __init__( self, id ):
        self.id = id

    def get( self, object ):
        if object is None: return None
        return dict(
            object.get_json(),
            iface_id=self.id,
            )

    def process_request( self, object, method, request ):
        if method == 'get':
            return object.iface.get(object)
        if method == 'run_command':
            command_id = request['command_id']
            response = object.run_command(command_id, request)
            if isinstance(response, Object):
                new_object = response
                response = new_object.iface.get(new_object)
            return response
        else:
            assert False, repr(method)  # Unknown method


class ObjectIface(Iface):

    def __init__( self ):
        Iface.__init__(self, 'object')


class TextObjectIface(Iface):

    def __init__( self ):
        Iface.__init__(self, 'text')


class ListIface(Iface):

    def __init__( self ):
        Iface.__init__(self, 'list')

    def get( self, object ):
        if object is None: return None
        elements, has_more = self.get_elements(object)
        return dict(
            Iface.get(self, object),
            columns=[column.as_json() for column in object.columns],
            elements=elements,
            has_more=has_more)

    def get_elements( self, object, count=None, key=None ):
        elements, has_more = object.get_elements(count, key)
        return ([elt.as_json() for elt in elements], has_more)

    def process_request( self, object, method, request ):
        if method == 'get_elements':
            key = request['key']
            count = request['count']
            elements, has_more = self.get_elements(object, count, key)
            return dict(elements=elements,
                        has_more=has_more)
        elif method == 'run_element_command':
            command_id = request['command_id']
            element_key = request['element_key']
            new_object = object.run_element_command(command_id, element_key)
            return new_object.iface.get(new_object)
        else:
            return Iface.process_request(self, object, method, request)
