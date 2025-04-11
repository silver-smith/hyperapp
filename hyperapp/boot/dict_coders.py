from .htypes.packet_coders import packet_coders
from .dict_encoder import JsonEncoder, YamlEncoder
from .dict_decoder import JsonDecoder, YamlDecoder


packet_coders.register('json', JsonEncoder, JsonDecoder)
packet_coders.register('yaml', YamlEncoder, YamlDecoder)
