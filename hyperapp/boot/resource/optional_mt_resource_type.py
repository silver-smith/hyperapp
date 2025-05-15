from ..htypes import (
    BUILTIN_MODULE_NAME,
    tString,
    TRecord,
    optional_mt,
    )
from ..dict_decoder import NamedPairsDictDecoder
from ..dict_encoder import NamedPairsDictEncoder


optional_def_mt = TRecord(BUILTIN_MODULE_NAME, 'optional_def_mt', {
    'base': tString,
    })


class OptionalMtResourceType:

    name = 'optional_mt'
    resource_t = optional_mt
    definition_t = optional_def_mt

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<ResourceType: {self.name!r}>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_path):
        return optional_mt(
            base=resolver(definition.base),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return optional_def_mt(
            base=resolver(resource.base),
            )
