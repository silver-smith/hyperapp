from .packet import Packet
from .json_encoder import JsonEncoder
from .json_decoder import JsonDecoder
from .cdr_encoder import CdrEncoder
from .cdr_decoder import CdrDecoder

    
class Coders(object):

    def __init__( self, encoder, decoder ):
        self.encoder = encoder  # constructor, no args
        self.decoder = decoder  # constructor, args: iface_registry, object_resolver (opt)


class PacketCoders(object):

    def __init__( self ):
        self.encodings = {}  # encoding -> Coders

    def register( self, encoding, encoder, decoder ):
        assert isinstance(encoding, str), repr(encoding)
        self.encodings[encoding] = Coders(encoder, decoder)

    def resolve( self, encoding ):
        assert encoding in self.encodings, repr(encoding)  # Unknown encoding
        return self.encodings[encoding]

    def decode( self, packet, t, iface_registry ):
        coders = self.resolve(packet.encoding)
        decoder = coders.decoder(iface_registry)
        return decoder.decode(t, packet.contents)

    def encode( self, encoding, object, t ):
        coders = self.resolve(encoding)
        encoder = coders.encoder()
        return Packet(encoding, encoder.encode(t, object))


packet_coders = PacketCoders()
packet_coders.register('json', JsonEncoder, JsonDecoder)
packet_coders.register('cdr', CdrEncoder, CdrDecoder)
