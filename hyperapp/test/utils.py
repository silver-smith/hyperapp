from hyperapp.common.packet_coders import packet_coders


BUNDLE_ENCODING = 'json'


def encode_bundle(services, bundle):
    return packet_coders.encode(BUNDLE_ENCODING, bundle, services.types.hyper_ref.bundle)

def decode_bundle(services, encoded_bundle):
    return packet_coders.decode(BUNDLE_ENCODING, encoded_bundle, services.types.hyper_ref.bundle)
