# Embedded type embed seamlessly into encoded data: json included as json, cdr as tBinary

import abc
from .htypes import Type
from ..packet_coders import packet_coders


class EncodableEmbedded(object):

    def __init__(self, t, value):
        self.type = t
        self.value = value

    def encode(self, encoding):
        return packet_coders.encode(encoding, self.value, self.type)

    def decode(self, t):
        assert t == self.type
        return self.value


class DecodableEmbedded(object, metaclass=abc.ABCMeta):

    def __init__(self, data):
        self.data = data

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


tEmbedded = TEmbedded()
