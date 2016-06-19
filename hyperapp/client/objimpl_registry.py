# object implementaion registry

from .registry import Registry


class ObjImplRegistry(Registry):

    def produce_obj( self, state ):
        rec = self._resolve(state.objimpl_id)
        return rec.factory(state, *rec.args, **rec.kw)


objimpl_registry = ObjImplRegistry()
