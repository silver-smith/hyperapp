#!/usr/bin/env python

import os.path
import sys
import argparse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


KEY_SIZE = 4096


def create_identity( fpath, overwrite ):
    private_fpath = fpath + '.identity.pem'
    public_fpath = fpath + '.public.pem'
    if os.path.exists(private_fpath) and not overwrite:
        print 'identity file %r is already exists' % private_fpath
        return
    if os.path.exists(public_fpath) and not overwrite:
        print 'identity file %r is already exists' % public_fpath
        return

    print 'generating rsa key of size %d...' % KEY_SIZE,
    sys.stdout.flush()
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=KEY_SIZE,
        backend=default_backend()
    )
    print ' ... done'

    public_key = private_key.public_key()

    with open(private_fpath, 'w') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
            ))
    print 'identity is written to %r' % private_fpath
    with open(public_fpath, 'w') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
    print 'public key is written to %r' % public_fpath

def main():
    parser = argparse.ArgumentParser(description='Generate new identity - public and private key pair, and store them to files')
    parser.add_argument('fpath', help='path to output files base')
    parser.add_argument('--overwrite', '-o', action='store_true', help='overwrite output files if they are exist')
    args = parser.parse_args()
    create_identity(args.fpath, args.overwrite)

main()
