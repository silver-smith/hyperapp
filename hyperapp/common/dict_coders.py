from .packet_coders import packet_coders
from .dict_encoders import JsonEncoder, YamlEncoder
from .dict_decoders import JsonDecoder, YamlDecoder


packet_coders.register('json', JsonEncoder('json'), JsonDecoder())
packet_coders.register('yaml', YamlEncoder('json'), YamlDecoder())
