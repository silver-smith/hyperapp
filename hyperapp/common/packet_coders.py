

class DecodeError(Exception):
    pass


class Coders(object):

    def __init__(self, encoder, decoder):
        self.encoder = encoder
        self.decoder = decoder


class PacketCoders(object):

    def __init__(self):
        self.encodings = {}  # encoding -> Coders

    def register(self, encoding, encoder, decoder):
        assert isinstance(encoding, str), repr(encoding)
        self.encodings[encoding] = Coders(encoder, decoder)

    def resolve(self, encoding):
        assert encoding in self.encodings, repr(encoding)  # Unknown encoding
        return self.encodings[encoding]

    def decode(self, encoding, data, t):
        coders = self.resolve(encoding)
        return coders.decoder.decode(t, data)

    def encode(self, encoding, object, t):
        coders = self.resolve(encoding)
        return coders.encoder.encode(t, object)


packet_coders = PacketCoders()
