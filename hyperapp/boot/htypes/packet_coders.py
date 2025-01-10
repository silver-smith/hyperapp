
from .deduce_value_type import deduce_value_type


class DecodeError(Exception):
    pass


class Coders(object):

    def __init__(self, encoder_ctr, decoder_ctr):
        self.encoder_ctr = encoder_ctr
        self.decoder_ctr = decoder_ctr


class PacketCoders(object):

    def __init__(self):
        self.encodings = {}  # encoding -> Coders

    def register(self, encoding, encoder_ctr, decoder_ctr):
        assert isinstance(encoding, str), repr(encoding)
        self.encodings[encoding] = Coders(encoder_ctr, decoder_ctr)

    def resolve(self, encoding):
        assert encoding in self.encodings, repr(encoding)  # Unknown encoding
        return self.encodings[encoding]

    def decode(self, encoding, data, t):
        coders = self.resolve(encoding)
        return coders.decoder_ctr().decode(t, data)

    def encode(self, encoding, object, t=None):
        t = t or deduce_value_type(object)
        assert isinstance(object, t), repr(object)
        coders = self.resolve(encoding)
        return coders.encoder_ctr().encode(object, t)


packet_coders = PacketCoders()
