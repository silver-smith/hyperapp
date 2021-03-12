from .record import ref_t


def phony_ref(ref_id):
    return ref_t('phony', ref_id.encode())

