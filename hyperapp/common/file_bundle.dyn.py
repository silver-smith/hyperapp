from hyperapp.common.htypes import bundle_t
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common.visual_rep import pprint


ENCODING = 'json'


def save_bytes_to_file(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def save_bundle_to_file(bundle, path):
    data = packet_coders.encode(ENCODING, bundle)
    save_bytes_to_file(data, path)

def load_bundle_from_file(path):
    bundle = packet_coders.decode(ENCODING, path.read_bytes(), bundle_t)
    pprint(bundle, title='Bundle loaded from %s:' % path)
    return bundle
