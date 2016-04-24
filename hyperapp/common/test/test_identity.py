import unittest
from hyperapp.common.identity import BadSignature, Identity


class IdentityTest(unittest.TestCase):

    def test_signature( self ):
        identity = Identity.generate()
        message = 'test message'
        signature = identity.sign(message)
        public_key = identity.get_public_key()
        public_key.verify(message, signature)
        self.assertRaises(BadSignature, public_key.verify, message, signature + 'x')
        self.assertRaises(BadSignature, public_key.verify, message + 'x', signature)
