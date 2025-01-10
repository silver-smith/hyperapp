from functools import partial

from ..boot.htypes.partial import (
    partial_param_t,
    partial_param_def_t,
    partial_t,
    partial_def_t,
    )
from ..boot.dict_decoder import NamedPairsDictDecoder
from ..boot.dict_encoder import NamedPairsDictEncoder


class PartialResourceType:

    resource_t = partial_t
    definition_t = partial_def_t

    def __str__(self):
        return 'partial'

    def __repr__(self):
        return "<ResourceType: 'partial'>"

    def from_dict(self, data):
        decoder = NamedPairsDictDecoder()
        return decoder.decode_dict(self.definition_t, data)

    def to_dict(self, definition):
        encoder = NamedPairsDictEncoder()
        return encoder.encode(definition)

    def resolve(self, definition, resolver, resource_dir):
        params = tuple(
            partial_param_t(
                name=rec.name,
                value=resolver(rec.value)
                )
            for rec in definition.params
            )
        return partial_t(
            function=resolver(definition.function),
            params=params,
            )

    def reverse_resolve(self, resource, resolver, resource_dir):
        params = tuple(
            partial_param_def_t(
                name=rec.name,
                value=resolver(rec.value)
                )
            for rec in resource.params
            )
        return partial_def_t(
            function=resolver(resource.function),
            params=params,
            )


def partial_pyobj(piece, pyobj_creg):
    fn = pyobj_creg.invite(piece.function)
    kw = {
        param.name: pyobj_creg.invite(param.value)
        for param in piece.params
        }
    return partial(fn, **kw)
