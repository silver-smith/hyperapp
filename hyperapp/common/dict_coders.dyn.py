from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.dict_encoders import JsonEncoder, YamlEncoder
from hyperapp.common.dict_decoders import JsonDecoder, YamlDecoder
from hyperapp.common.module import Module


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        packet_coders.register('json', JsonEncoder(), JsonDecoder())
        packet_coders.register(
            'yaml',
            YamlEncoder(services.types),
            YamlDecoder(services.ref_registry, services.types),
            )
