#!/usr/bin/env python3

import os.path
import logging
import argparse
from pathlib import Path

from hyperapp.common.htypes import (
    TList,
    tTypeDef,
    tTypeModule,
    make_builtins_type_namespace,
    )    
#from hyperapp.common.visual_rep import pprint
from hyperapp.common.type_module_parser import Lexer, load_type_module

log = logging.getLogger(__name__)


def test_lex(fpaths):
    for fpath in fpaths:
        log.info('%s:' % fpath)
        lexer = Lexer()
        input = fpath.read_text()
        lexer.input(input)
        while True:
            tok = lexer.token()
            log.info(tok)
            if not tok:
                break

def test_yacc(fpaths):
    builtins = make_builtins_type_namespace()
    for fpath in fpaths:
        log.info('%s:', fpath)
        module_name = fpath.stem
        log.info('loading %s:', module_name)
        module = load_type_module(builtins, module_name, fpath, debug=True)
        log.info('%d imports:', len(module.import_list))
        for imp in module.import_list:
            log.info('\t%s.%s', imp.module_name, imp.name)
        log.info('%d typedefs:', len(module.typedefs))
        for typedef in module.typedefs:
            log.info('\t%s: %s', typedef.name, typedef.type)
        #pprint(module)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')

    parser = argparse.ArgumentParser(description='Hyperapp types file parser test')
    parser.add_argument('command', choices=['lex', 'yacc'], help='What to test')
    parser.add_argument('fpaths', type=Path, nargs='+', help='Type files to parse')
    args = parser.parse_args()

    if args.command == 'lex':
        test_lex(args.fpaths)
    elif args.command == 'yacc':
        test_yacc(args.fpaths)
    
main()
