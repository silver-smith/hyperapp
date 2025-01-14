from ..htypes.call import call_t, call_def_t
from ..dict_decoder import NamedPairsDictDecoder
from ..dict_encoder import NamedPairsDictEncoder


class CallResourceType:

    resource_t = call_t
    definition_t = call_def_t

    def __str__(self):
        return 'call'

    def __repr__(self):
        return "<ResourceType: 'call'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        return call_t(
            function=resolver(definition.function),
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        return call_def_t(
            function=resolver(resource.function),
            )


def call_pyobj(piece, pyobj_creg):
    fn = pyobj_creg.invite(piece.function)
    return fn()
