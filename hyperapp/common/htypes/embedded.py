# Embedded type embed seamlessly into encoded data: json included as json, cdr as tBinary

import abc
from .htypes import Type
from .packet_coders import packet_coders


class EncodableEmbedded(object):

    def __init__(self, t, value):
        assert isinstance(value, t)
        self.type = t
        self.value = value

    def __repr__(self):
        return '<EncodableEmbedded: %r>' % self.value

    def __hash__(self):
        return hash((self.type, self.value))

    def encode(self, encoding):
        return packet_coders.encode(encoding, self.value, self.type)

    def decode(self, t=None):
        assert t is None or t == self.type
        return self.value


class DecodableEmbedded(object, metaclass=abc.ABCMeta):

    def __init__(self, data):
        self.data = data

    def __hash__(self):
        return hash(self.data)

    @abc.abstractmethod
    def decode(self, t):
        pass


class TEmbedded(Type):

    def __repr__(self):
        return '<TEmbedded>'

    def __eq__(self, other):
        return isinstance(other, TEmbedded)

    def __instancecheck__(self, value):
        return isinstance(value, (EncodableEmbedded, DecodableEmbedded))

    def instance_hash(self, value):
        return hash(value)


tEmbedded = TEmbedded(['builtins', 'embedded'])
