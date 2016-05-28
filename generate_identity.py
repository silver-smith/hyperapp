#!/usr/bin/env python3

import os.path
import sys
import logging
import argparse
from hyperapp.common.identity import RSA_KEY_SIZE_SAFE, Identity

log = logging.getLogger(__name__)


def create_identity( fpath, overwrite ):
    private_fpath = fpath + '.identity.pem'
    public_fpath = fpath + '.public.pem'
    if os.path.exists(private_fpath) and not overwrite:
        log.info('identity file %r is already exists', private_fpath)
        return
    if os.path.exists(public_fpath) and not overwrite:
        log.info('identity file %r is already exists', public_fpath)
        return

    log.info('generating rsa key of size %d...', RSA_KEY_SIZE_SAFE)
    sys.stdout.flush()
    identity = Identity.generate()
    log.info('generating rsa key ... done')

    public_key = identity.private_key.public_key()
    identity.save_to_file(private_fpath)
    log.info('identity is written to %r', private_fpath)
    identity.get_public_key().save_to_file(public_fpath)
    log.info('public key is written to %r', public_fpath)

def main():
    parser = argparse.ArgumentParser(description='Generate new identity - public and private key pair, and store them to files')
    parser.add_argument('fpath', help='path to output files base')
    parser.add_argument('--overwrite', '-o', action='store_true', help='overwrite output files if they are exist')
    args = parser.parse_args()
    create_identity(args.fpath, args.overwrite)

main()
