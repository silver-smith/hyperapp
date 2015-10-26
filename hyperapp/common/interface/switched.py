# record with some field is of variable type, switched by other field values

from ..util import is_list_inst, is_tuple_inst
from .iface_types import join_path, Type, Field, TRecord


class TSwitchedField(Type):

    def validate( self, path, value ):
        pass


tSwitchedField = TSwitchedField()


class TSwitched(TRecord):

    def __init__( self, dynamic_field, switches, fields ):
        assert isinstance(dynamic_field, str), repr(dynamic_field)  # field name is expected
        assert is_list_inst(switches, str), repr(switches)  # field name list is expected
        TRecord.__init__(self, fields)
        assert self._pick_field(dynamic_field).type is tSwitchedField  # dynamic field's type must be tSwitchedField
        self.dynamic_field = self._pick_field(dynamic_field)
        self.switches = []  # switch field name list
        self.registry = {}  # switch values tuple -> type

    def get_static_fields( self ):
        return [field for self.get_fields() if field is not self.dynamic_field]

    # get Field with actual dynamic type
    def get_dynamic_field( self, static_fields_dict ):
        switch = self._pick_switch(static_fields_dict)
        type = self._resolve(switch)
        return Field(self.dynamic_field.name, type)

    def _pick_field( self, name ):
        for field in self.fields:
            if field.name == name:
                return field
        assert False, repr(name)  # Field is missing

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
