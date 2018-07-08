import os.path
from pathlib import Path

from .interface import hyper_ref as href_types
from .packet_coders import packet_coders


LOCAL_REF_RESOLVER_REF_PATH = Path('~/.local/share/hyperapp/common/local_ref_resolver.ref.json').expanduser()
LOCAL_SERVER_MANAGEMENT_REF_LIST_REF_PATH = Path('~/.local/share/hyperapp/common/local_server_management_ref_list.ref.json').expanduser()
ENCODING = 'json'


def save_bytes_to_file(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def save_bundle_to_file(bundle, path):
    data = packet_coders.encode(ENCODING, bundle, href_types.bundle)
    save_bytes_to_file(data, path)

def load_bundle_from_file(path):
    return packet_coders.decode(ENCODING, path.read_bytes(), href_types.bundle)
