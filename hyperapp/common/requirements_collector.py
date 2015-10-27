from .method_dispatch import method_dispatch
from .interface import (
    TPrimitive,
    TOptional,
    TRecord,
    THierarchy,
    TList,
    tObject,
    tProxyObject,
    tHandle,
    tViewHandle,
    )


class RequirementsCollector(object):

    def collect( self, t, value ):
        self.collected_requirements = set()
        self.dispatch(t, value)
        return list([registry, key] for registry, key in self.collected_requirements)

    @method_dispatch
    def dispatch( self, t, value ):
        assert False, repr((t, value))  # Unknown type

    @dispatch.register(TPrimitive)
    def process_primitive( self, t, value ):
        pass

    @dispatch.register(TOptional)
    def process_optional( self, t, value ):
        if value is not None:
            self.dispatch(t.type, value)

    @dispatch.register(TRecord)
    def process_record( self, t, value ):
        base_fields = set()
        while True:
            new_fields = [field for field in t.get_fields() if field.name not in base_fields]
            for field in new_fields:
                self.process_field(field, value)
            if not isinstance(t, TDynamicRec):
                break
            base_fields = set(field.name for field in t.get_fields())
            t = t.resolve_dynamic(value)
            
    @dispatch.register(THierarchy)
    def process_hierarchy_obj( self, t, value ):
        if t is tObject:
            self.collected_requirements.add(('object', value.objimpl_id))
            if tObject.isinstance(value, tProxyObject):
                self.collected_requirements.add(('interface', value.iface.iface_id))
        if t is tHandle and tHandle.isinstance(value, tViewHandle):
            self.collected_requirements.add(('handle', value.view_id))
        tclass = t.resolve_obj(value)
#        self.collected_requirements.add((t.hierarchy_id, tclass.id))
        for field in tclass.get_fields():
            self.process_field(field, value)

    def process_field( self, field, value ):
        self.dispatch(field.type, getattr(value, field.name))

    @dispatch.register(TList)
    def process_list( self, t, value ):
        for elt in value:
            self.dispatch(t.element_type, elt)
