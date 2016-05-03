from ..common.interface.form import tStringFieldHandle, tIntFieldHandle


def stringFieldHandle( value=None ):
    return tStringFieldHandle('string', value or '')

def intFieldHandle( value ):
    return tIntFieldHandle('int', value)

