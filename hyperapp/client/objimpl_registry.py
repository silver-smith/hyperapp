# object implementaion registry


class ObjImplRegistry(object):

    def __init__( self ):
        self.id2impl = {}  # objimpl_id -> object implementation instance factory/producer

    def register( self, objimpl_id, producer ):
        self.id2impl[objimpl_id] = producer

    def is_registered( self, objimpl_id ):
        return objimpl_id in self.id2impl

    def produce_obj( self, objinfo, server=None ):
        producer = self.id2impl.get(objinfo.objimpl_id)
        assert producer is not None, repr(objinfo.objimpl_id)  # Unknown objimpl_id
        return producer(objinfo, server)


objimpl_registry = ObjImplRegistry()
