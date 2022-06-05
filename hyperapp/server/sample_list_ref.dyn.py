from .htypes.sample_list import sample_list
from .services import local_server_ref


def save_sample_list_ref():
    local_server_ref.save_piece(sample_list(provider='server'))
