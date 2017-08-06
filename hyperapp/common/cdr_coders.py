from .packet_coders import packet_coders
from .cdr_encoder import CdrEncoder
from .cdr_decoder import CdrDecoder


packet_coders.register('cdr', CdrEncoder(), CdrDecoder())
