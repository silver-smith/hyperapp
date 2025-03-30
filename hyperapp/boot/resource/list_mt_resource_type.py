from ..htypes import (
    BUILTIN_MODULE_NAME,
    tString,
    TRecord,
    list_mt,
    )
from ..dict_decoder import NamedPairsDictDecoder
from ..dict_encoder import NamedPairsDictEncoder


list_def_mt = TRecord(BUILTIN_MODULE_NAME, 'list_def_mt', {
    'element': tString,
    })


class ListMtResourceType:

    name = 'list_mt'
    resource_t = list_mt
    definition_t = list_def_mt

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
        return list_mt(
            element=resolver(definition.element),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return list_def_mt(
            element=resolver(resource.element),
            )
