from functools import cached_property

from hyperapp.boot.htypes import ref_t, builtin_mt, list_mt, optional_mt, field_mt, record_mt, exception_mt
from hyperapp.boot.mapper import Mapper
from hyperapp.boot.dict_decoder import NamedPairsDictDecoder
from hyperapp.boot.dict_encoder import NamedPairsDictEncoder


class TypeToDefinitionMapper(Mapper):

    def __init__(self, mosaic, web):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self.type_meta_to_def_meta = {}

    def process_record(self, t, value, context):
        fields = self.map_record_fields(t, value, context)
        is_named = t in {record_mt, exception_mt}
        if is_named:
            fields = {**fields, 'name': fields['name'] + '_def'}
        mapped_value = t(**fields)
        if is_named:
            self.type_meta_to_def_meta[value] = mapped_value
        if t is ref_t:
            return self._map_type_ref(mapped_value)
        if t is builtin_mt and mapped_value.name == 'ref':
            return builtin_mt(name='string')
        return mapped_value

    def _map_type_ref(self, value):
        referred_value = self._web.summon(value)
        mapped_value = self.map(referred_value)
        return self._mosaic.put(mapped_value)


class TypeToValueMapper(Mapper):

    def __init__(self, mosaic, web, pyobj_creg, source_meta_to_target_meta):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._pyobj_creg = pyobj_creg
        self._source_meta_to_target_meta = source_meta_to_target_meta

    def process_record(self, t, value, context):
        if t is ref_t:
            return self._map_type_ref(value, context)
        if t is record_mt:
            return self._map_record(value)
        if t is list_mt:
            return ListMapper(self.map(value.element))
        if t is optional_mt:
            return OptionalMapper(self.map(value.base))
        if t is builtin_mt:
            if value.name == 'ref':
                return ResolveMapper()
            else:
                return IdentityMapper()
        raise RuntimeError(f"Unknown meta type {t}: {value}")

    def _map_record(self, value):
        if value.base:
            base_record = self._web.summon(value.base)
            base_mapper = self.map(base_record)
        else:
            base_mapper = None
        target_t_meta = self._source_meta_to_target_meta[value]
        target_t = self._pyobj_creg.animate(target_t_meta)
        fields = {
            f.name: self.map(f.type)
            for f in value.fields
            }
        return RecordMapper(target_t, fields, base_mapper)

    def _map_type_ref(self, value, context):
        referred_value = self._web.summon(value)
        return self.map(referred_value, context=context)


class RecordMapper:

    def __init__(self, target_t, field_mappers, base_mapper=None):
        self._target_t = target_t
        self._field_mappers = field_mappers
        if base_mapper:
            self._field_mappers.update(base_mapper._field_mappers)

    def map(self, resolver, value):
        fields = {
            name: mapper.map(resolver, getattr(value, name))
            for name, mapper in self._field_mappers.items()
            }
        return self._target_t(**fields)


class OptionalMapper:

    def __init__(self, base_mapper):
        self._base_mapper = base_mapper

    def map(self, resolver, value):
        if value is None:
            return None
        return self._base_mapper.map(resolver, value)


class ListMapper:

    def __init__(self, base_mapper):
        self._base_mapper = base_mapper

    def map(self, resolver, value):
        return tuple(self._base_mapper.map(resolver, item) for item in value)


class IdentityMapper:

    def map(self, resolver, value):
        return value


class ResolveMapper:

    def map(self, resolver, value):
        return resolver(value)


class ResourceType:

    def __init__(self, mosaic, web, pyobj_creg, resource_t):
        self._mosaic = mosaic
        self._web = web
        self._pyobj_creg = pyobj_creg
        self.resource_t = resource_t

        self._resource_type_mt = self._pyobj_creg.actor_to_piece(self.resource_t)

        mapper = TypeToDefinitionMapper(self._mosaic, self._web)
        definition_type = mapper.map(self._resource_type_mt)
        self._type_meta_to_def_meta = mapper.type_meta_to_def_meta
        self._type_meta_to_type_meta = {
            key: key for key in mapper.type_meta_to_def_meta.keys()
            }
        self.definition_t = self._pyobj_creg.animate(definition_type)

    def __str__(self):
        return str(self.resource_t)

    def __repr__(self):
        return f"<ResourceType {self}>"

    def __eq__(self, rhs):
        return (self is rhs or
                isinstance(rhs, ResourceType) and self.resource_t == rhs.resource_t)

    def __lt__(self, rhs):
        return self.resource_t < rhs.resource_t

    def __hash__(self):
        return hash(self.resource_t)

    @cached_property
    def _mapper(self):
        type_mapper = TypeToValueMapper(self._mosaic, self._web, self._pyobj_creg, self._type_meta_to_type_meta)
        return type_mapper.map(self._resource_type_mt)

    @cached_property
    def _reverse_mapper(self):
        type_mapper = TypeToValueMapper(self._mosaic, self._web, self._pyobj_creg, self._type_meta_to_def_meta)
        return type_mapper.map(self._resource_type_mt)

    def resolve(self, value, resolver, resource_dir):
        return self._mapper.map(resolver, value)

    def reverse_resolve(self, value, resolver, resource_dir):
        return self._reverse_mapper.map(resolver, value)

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition, self.definition_t)
