# object implementaion registry


class ObjImplRegistry(object):

    def __init__( self ):
        self.id2impl = {}  # objimpl_id -> object implementation instance factory

    def register( self, factory ):
        self.id2impl[cls.get_objimpl_id()] = factory

    def is_registered( self, objimpl_id ):
        return objimpl_id in self.id2impl

    def factory( self, objinfo ):
        factory = self.id2impl.get(objinfo.objimpl_id)
        assert factory is not None, repr(objinfo.objimpl_id)  # Unknown objimpl_id
        return factory(objinfo)


objimpl_registry = ObjImplRegistry()
