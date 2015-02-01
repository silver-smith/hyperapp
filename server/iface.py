from object import Object


class Iface(object):

    def __init__( self, id ):
        self.id = id


class ObjectIface(Iface):

    def __init__( self ):
        Iface.__init__(self, 'object')


class TextObjectIface(Iface):

    def __init__( self ):
        Iface.__init__(self, 'text')


class ListIface(Iface):

    def __init__( self, id='list' ):
        Iface.__init__(self, id)
