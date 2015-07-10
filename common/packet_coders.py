from . packet import Packet
from . json_encoder import JsonEncoder
from . json_decoder import JsonDecoder

    
class Coders(object):

    def __init__( self, encoder, decoder ):
        self.encoder = encoder  # constructor, no args
        self.decoder = decoder  # constructor, args: peer, iface_registry, object_resolver (opt)


class PacketCoders(object):

    def __init__( self ):
        self.encodings = {}  # encoding -> Coders

    def register( self, encoding, encoder, decoder ):
        assert isinstance(encoding, str), repr(encoding)
        self.encodings[encoding] = Coders(encoder, decoder)

    def resolve( self, encoding ):
        assert encoding in self.encodings, repr(encoding)  # Unknown encoding
        return self.encodings[encoding]

    def decode( self, packet, t, peer, iface_registry, object_resolver=None ):
        coders = self.resolve(packet.encoding)
        decoder = coders.decoder(peer, iface_registry, object_resolver)
        return decoder.decode(t, packet.contents)

    def encode( self, encoding, object, t ):
        coders = self.resolve(encoding)
        encoder = coders.encoder()
        return Packet(encoding, encoder.encode(t, object))


packet_coders = PacketCoders()
packet_coders.register('json', JsonEncoder, JsonDecoder)
