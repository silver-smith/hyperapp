from functools import cached_property, partial

from hyperapp.common.htypes import ref_t, builtin_mt, name_wrapped_mt, field_mt, record_mt
from hyperapp.common.mapper import Mapper
from hyperapp.common.dict_decoders import NamedPairsDictDecoder
from hyperapp.common.dict_encoders import NamedPairsDictEncoder
from hyperapp.common.module import Module


class RefToStringMapper(Mapper):

    def __init__(self, mosaic, web):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self.path_set = set()
        self.path_to_record_t_ref = {}

    def process_record(self, t, value, context):
        if t is name_wrapped_mt:
            self.path_to_record_t_ref[context[2]] = self._mosaic.put(value)
        if t is field_mt:
            fields_context = (False, (*context[1], value.name), (*context[2], value.name))
        elif t is record_mt:
            fields_context = (True, context[1], context[2])
        else:
            fields_context = (False, context[1], context[2])
        fields = self.map_record_fields(t, value, fields_context)
        mapped_value = t(**fields)
        if t is ref_t:
            return self.map_type_ref(mapped_value, context)
        if t is builtin_mt and mapped_value.name == 'ref':
            return self.map_builtin_ref(mapped_value, context)
        return mapped_value

    def map_type_ref(self, value, context):
        referred_value = self._web.summon(value)
        mapper = RefToStringMapper(self._mosaic, self._web)
        mapped_value = mapper.map(referred_value, context=context)
        self.path_set |= mapper.path_set
        self.path_to_record_t_ref.update(mapper.path_to_record_t_ref)
        return self._mosaic.put(mapped_value)

    def map_builtin_ref(self, value, context):
        self.path_set.add(context[1])
        return builtin_mt(name='string')

    def field_context(self, context, name, value):
        if context[0] and name == 'base':
            # This is record_mt 'base', field.
            # Add path to second context so that supertypes do not overwrite subtypes at path_to_record_t_ref mapping.
            return (False, context[1], (*context[2], 'record_base'))
        else:
            return (False, context[1], context[2])


class NameResolver(Mapper):

    def __init__(self, ref_path_set, path_to_record_t, resolve_name):
        super().__init__()
        self._ref_path_set = ref_path_set
        self._path_to_record_t = path_to_record_t
        self._resolve_name = resolve_name

    def process_record(self, t, value, context):
        fields = self.map_record_fields(t, value, context)
        result_t = self._path_to_record_t[context]
        result = result_t(**fields)
        return self.map_record(t, result, context)

    def process_primitive(self, t, value, context):
        if context in self._ref_path_set:
            return self._resolve_name(value)
        else:
            return value

    def field_context(self, context, name, value):
        return (*context, name)


class ResourceType:

    def __init__(self, types, mosaic, web, resource_t):
        self._types = types
        self._mosaic = mosaic
        self._web = web
        self.resource_t = resource_t

        resource_type_ref = self._types.reverse_resolve(self.resource_t)
        resource_type = self._web.summon(resource_type_ref)
        mapper = RefToStringMapper(self._mosaic, self._web)
        definition_type = mapper.map(resource_type, context=(False, (), ()))
        definition_type_ref = self._mosaic.put(definition_type)

        self._ref_path_set = mapper.path_set
        self._path_to_record_t = {
            path: self._types.resolve(type_ref)
            for path, type_ref
            in mapper.path_to_record_t_ref.items()
            }
        self.definition_t = self._types.resolve(definition_type_ref)

    def __str__(self):
        return str(self.resource_t)

    def __repr__(self):
        return f"<ResourceType {self}>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolve_name, resource_dir):
        resolver = NameResolver(self._ref_path_set, self._path_to_record_t, resolve_name)
        return resolver.map(definition, context=())


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_factory = partial(ResourceType, services.types, services.mosaic, services.web)
