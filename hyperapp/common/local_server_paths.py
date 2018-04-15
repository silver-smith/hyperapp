import os.path
from pathlib import Path

from .interface import hyper_ref as href_types
from .packet_coders import packet_coders


LOCAL_REF_RESOLVER_REF_PATH = Path('~/.local/share/hyperapp/common/local_ref_resolver.ref.json').expanduser()
LOCAL_SERVER_REF_LIST_REF_PATH = Path('~/.local/share/hyperapp/common/local_server_ref_list.ref.json').expanduser()
ENCODING = 'json'


def save_bytes_to_file(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def save_parcel_to_file(parcel, path):
    data = packet_coders.encode(ENCODING, parcel, href_types.parcel)
    save_bytes_to_file(data, path)

def load_parcel_from_file(path):
    return packet_coders.decode(ENCODING, path.read_bytes(), href_types.parcel)
