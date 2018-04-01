import unittest
from hyperapp.common.identity import Identity


class IdentityTest(unittest.TestCase):

    def test_signature(self):
        identity = Identity.generate(fast=True)
        message = b'test message'
        signature = identity.sign(message)
        public_key = identity.public_key
        self.assertEqual(True, public_key.verify(message, signature))
        self.assertEqual(False, public_key.verify(message, signature + b'x'))
        self.assertEqual(False, public_key.verify(message + b'x', signature))
