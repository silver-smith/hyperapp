#!/usr/bin/env python3

import sys
from pathlib import Path

import yaml


def modify_definitions(data):
    definitions = data.get('definitions')
    if not definitions:
        return data
    new_definitions = {}
    for name, value in definitions.items():
        t = value.pop('_type')
        new_value = {
            'type': t,
            'value': value,
            }
        new_definitions[name] = new_value
    return {
        'import': data.get('import', []),
        'associations': data.get('associations', []),
        'definitions': new_definitions,
        }


def upgrade_resource(path):
    print(f"Upgrade: {path}")
    text = path.read_text()
    if text.startswith('#'):
        prefix_lines = text.splitlines()[:2]
    else:
        prefix_lines = None
    data = yaml.safe_load(text)
    upgraded_data = modify_definitions(data)
    upgraded_text = yaml.dump(upgraded_data, sort_keys=False)
    if prefix_lines:
        upgraded_text = '\n'.join(prefix_lines) + '\n' + upgraded_text
    path.write_text(upgraded_text)


def main():
    count = 0
    for dir in sys.argv[1:]:
        for path in Path(dir).rglob('*.resources.yaml'):
            upgrade_resource(path)
            count += 1
    print(f"Total: {count} resources upgraded")


if __name__ == '__main__':
    main()
