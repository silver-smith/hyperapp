from functools import cached_property, partial

from hyperapp.common.htypes import TList, TRecord, tString, ref_t, builtin_mt
from hyperapp.common.mapper import Mapper
from hyperapp.common.dict_decoders import DictDecoder, join_path
from hyperapp.common.module import Module


class RefToStringMapper(Mapper):

    def __init__(self, mosaic, web):
        super().__init__()
        self._mosaic = mosaic
        self._web = web

    def map_record(self, t, value):
        if t is not ref_t:
            return value
        mapper = RefToStringMapper(self._mosaic, self._web)
        referred_value = self._web.summon(value)
        if referred_value._t is builtin_mt and referred_value.name == 'ref':
            mapped_value = builtin_mt(name='string')
        else:
            mapped_value = mapper.map(referred_value)
        return self._mosaic.put(mapped_value)


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

    @cached_property
    def definition_t(self):
        resource_type_ref = self._types.reverse_resolve(self.resource_t)
        resource_type = self._web.summon(resource_type_ref)
        mapper = RefToStringMapper(self._mosaic, self._web)
        definition_type = mapper.map(resource_type)
        definition_type_ref = self._mosaic.put(definition_type)
        return self._types.resolve(definition_type_ref)

    def parse(self, data):
        decoder = DefinitionDecoder()
        return decoder.decode_dict(self.definition_t, data)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.resource_type_factory = partial(ResourceType, services.types, services.mosaic, services.web)
