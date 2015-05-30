
def is_list_inst( val, cls ):
    if not isinstance(val, list):
        return False
    for elt in val:
        if not isinstance(elt, cls):
            return False
    return True


def path2str( path ):
    return ','.join('%s=%s' % (key, value) for key, value in sorted(path.items()))
