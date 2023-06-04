from .htypes.pyobj_association import python_object_association_t, python_object_association_def_t
from .dict_decoders import NamedPairsDictDecoder
from .dict_encoders import NamedPairsDictEncoder


class PyObjAssociationResourceType:

    resource_t = python_object_association_t
    definition_t = python_object_association_def_t

    def __str__(self):
        return 'python_object_association'

    def __repr__(self):
        return "<ResourceType: 'python_object_association'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        return python_object_association_t(
            t=resolver(definition.t),
            function=resolver(definition.function),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return python_object_association_def_(
            t=resolver(definition.t),
            function=resolver(definition.function),
            )
