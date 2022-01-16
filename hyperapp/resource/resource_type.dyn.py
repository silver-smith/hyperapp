from functools import cached_property

from hyperapp.common.htypes import ref_t, builtin_mt
from hyperapp.common.mapper import Mapper


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
