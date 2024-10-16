from ..common.htypes.raw import raw_t, raw_def_t
from ..common.dict_decoder import NamedPairsDictDecoder
from ..common.dict_encoder import NamedPairsDictEncoder


class RawResourceType:

    resource_t = raw_t
    definition_t = raw_def_t

    def __str__(self):
        return 'raw'

    def __repr__(self):
        return "<ResourceType: 'raw'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        return raw_t(
            resource=resolver(definition.function),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return raw_def_t(
            resource=resolver(resource.function),
            )


def raw_pyobj(piece, web):
    return web.summon(piece.resource)
