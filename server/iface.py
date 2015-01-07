

class Iface(object):

    id = None

    def get( self, object ):
        return dict(
            iface_id=self.id,
            path=object.path,
            dir_commands=[cmd.as_json() for cmd in object.get_commands()],
            )


class ListIface(Iface):

    id = 'list'

    def get( self, object ):
        return dict(
            Iface.get(self, object),
            columns=[column.as_json() for column in object.columns],
            elements=self.get_elements(object))

    def get_elements( self, object, count=None, key=None ):
        return [elt.as_json() for elt in object.get_elements(count, key)]
