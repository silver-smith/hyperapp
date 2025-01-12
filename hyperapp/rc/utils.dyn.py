import re


# https://stackoverflow.com/a/1176023 Camel case to snake case.
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def iter_types(types):
    for module_name, name_to_piece in types.items():
        for name, piece in name_to_piece.items():
            yield (module_name, name, piece)
