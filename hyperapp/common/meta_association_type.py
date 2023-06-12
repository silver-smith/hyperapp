from .htypes.meta_association import meta_association_t, meta_association_def_t
from .dict_decoders import NamedPairsDictDecoder
from .dict_encoders import NamedPairsDictEncoder


class MetaAssociationResourceType:

    resource_t = meta_association_t
    definition_t = meta_association_def_t

    def __str__(self):
        return 'meta_association'

    def __repr__(self):
        return "<ResourceType: 'meta_association'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        return meta_association_t(
            t=resolver(definition.t),
            fn=resolver(definition.fn),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return meta_association_def_t(
            t=resolver(resource.t),
            fn=resolver(resource.fn),
            )
