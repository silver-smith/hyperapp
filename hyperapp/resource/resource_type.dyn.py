from functools import cached_property, partial

from hyperapp.common.htypes import TList, TRecord, tString, ref_t, builtin_mt, name_wrapped_mt, field_mt
from hyperapp.common.mapper import Mapper
from hyperapp.common.dict_decoders import DictDecoder, join_path
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
            self.path_to_record_t_ref[context] = self._mosaic.put(value)
        if t is field_mt:
            fields_context = (*context, value.name)
        else:
            fields_context = context
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
        self.path_set.add(context)
        return builtin_mt(name='string')


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


class DefinitionDecoder(DictDecoder):

    def decode_list(self, t, value, path):
        if (type(value) is dict
            and isinstance(t, TList)
            and isinstance(t.element_t, TRecord)
            and len(t.element_t.fields) == 2
            and list(t.element_t.fields.values())[0] is tString):
            return self._decode_list_dict(t.element_t, value, path)
        return super().decode_list(t, value, path)

    def _decode_list_dict(self, element_t, list_value, path):
        key_t, value_t = element_t.fields.values()
        result = []
        for idx, (key, raw_value) in enumerate(list_value.items()):
            value = self.dispatch(value_t, raw_value, join_path(path, f'#{idx}', 'value'))
            result.append(element_t(key, value))
        return result


class ResourceType:

    def __init__(self, types, mosaic, web, resource_t):
        self._types = types
        self._mosaic = mosaic
        self._web = web
        self.resource_t = resource_t

        resource_type_ref = self._types.reverse_resolve(self.resource_t)
        resource_type = self._web.summon(resource_type_ref)
        mapper = RefToStringMapper(self._mosaic, self._web)
        definition_type = mapper.map(resource_type, context=())
        definition_type_ref = self._mosaic.put(definition_type)

        self._ref_path_set = mapper.path_set
        self._path_to_record_t = {
            path: self._types.resolve(type_ref)
            for path, type_ref
            in mapper.path_to_record_t_ref.items()
            }
        self.definition_t = self._types.resolve(definition_type_ref)

    def parse(self, data):
        decoder = DefinitionDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def resolve(self, definition, resolve_name):
        resolver = NameResolver(self._ref_path_set, self._path_to_record_t, resolve_name)
        return resolver.map(definition, context=())


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_factory = partial(ResourceType, services.types, services.mosaic, services.web)
