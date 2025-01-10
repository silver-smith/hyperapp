from .htypes.packet_coders import packet_coders
from .dict_encoder import JsonEncoder
from .dict_decoder import JsonDecoder


packet_coders.register('json', JsonEncoder, JsonDecoder)
