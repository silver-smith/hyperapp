# record with some field is of variable type, switched by other field values

from ..util import is_list_inst, is_tuple_inst
from .iface_types import join_path, Type, Field, TRecord


class TSwitched(Type):

    def validate( self, path, value ):
        pass


tSwitched = TSwitched()


class TSwitchedRec(TRecord):

    def __init__( self, switches=None, fields=None, base=None ):
        assert isinstance(dynamic_field, str), repr(dynamic_field)  # field name is expected
        if switches is None:
            assert isinstance(base, TSwitchedRec)  # either switches must be defined, or base must be a TSwitchedRec
            self.switches = base.switches  # switch field name list
        else:
            assert is_list_inst(switches, str), repr(switches)  # field name list is expected
            self.switches = switches
        TRecord.__init__(self, fields, base)
        self.dynamic_field = self._pick_dynamic_field()
        self.registry = {}  # switch values tuple -> type

    def get_static_fields( self ):
        return [field for self.get_fields() if field is not self.dynamic_field]

    # get Field with actual dynamic type
    def get_dynamic_field( self, static_fields_dict ):
        switch = self._pick_switch(static_fields_dict)
        type = self._resolve(switch)
        return Field(self.dynamic_field.name, type)

    def _pick_dynamic_field( self ):
        dynamic_field = None
        for field in self.fields:
            if field.type is tSwitched:
                assert dynamic_field is None, repr((dynamic_field.name, field.name))  # only one dynamic field is supported
                dynamic_field = field
        assert dynamic_field is not None  # one field with type=tSwitched is expected
        return dynamic_field

    def _pick_switch( self, fields_dict ):
        return tuple(fields_dict[name] for name in selt.switches)

    def register( self, switches, type ):
        assert is_tuple_inst(switches, str), repr(switches)  # field
        assert switches not in self.registry, switches  # Duplicate
        self.registry[switches] = type

    def _resolve( self, switch ):
        type = self.registry.get(switch)
        assert type is not None, repr(switch)  # Unregistered type
        return type

    def adopt_args( self, args, kw, check_unexpected=True ):
        adopted_args = TRecord.adopt_args(self, args, kw, check_unexpected)
        switch = self._pick_switch(adopted_args)
        type = self._resolve(switch)
        dyn_name = self.dynamic_field.name
        type.validate(join_path('<TSwitched>', dyn_name), adopted_args[dyn_name])
        return adopted_args
