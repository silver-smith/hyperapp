from ..htypes.attribute import attribute_t, attribute_def_t
from ..dict_decoder import NamedPairsDictDecoder
from ..dict_encoder import NamedPairsDictEncoder


class AttributeResourceType:

    resource_t = attribute_t
    definition_t = attribute_def_t

    def __str__(self):
        return 'attribute'

    def __repr__(self):
        return "<ResourceType: 'attribute'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        return attribute_t(
            object=resolver(definition.object),
            attr_name=definition.attr_name,
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return attribute_def_t(
            object=resolver(resource.object),
            attr_name=resource.attr_name,
            )


def attribute_pyobj(piece, pyobj_creg):
    object = pyobj_creg.invite(piece.object)
    return getattr(object, piece.attr_name)
