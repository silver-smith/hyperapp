from .services import (
    reconstructors,
    )
from .code.type_reconstructor import type_to_piece
from .code.data_reconstructor import data_to_piece


def register_reconstructors():
    reconstructors.extend([
        type_to_piece,
        data_to_piece,
        ])
