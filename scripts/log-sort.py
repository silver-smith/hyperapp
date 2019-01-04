#!/usr/bin/env python3

# Process output of pytest - sort log lines by datetime within pytest sections, preserving order of lines with same datetime.

import sys
import re


LOG_RE = re.compile(r'^(\d{2}:\d{2}.\d{3}) ')
PYTEST_SECTION_RE = re.compile(r'^\-+ Captured log \w+ \-+')
SEPARATOR_RE = re.compile('^(\d{2}:\d{2}.\d{3}) [^-]+(\-+ [\w ]+ \-+)')


def main():
    key2lines = {}

    def flush():
        for key in sorted(key2lines):
            for line in key2lines[key]:
                print(line, end='')
        key2lines.clear()

    def push_line(key, line):
        lines = key2lines.setdefault(mo.group(1), [])
        lines.append(line)

    for line in sys.stdin:
        mo = SEPARATOR_RE.match(line)
        if mo:
            push_line(mo.group(1), mo.group(2) + '\n')
            continue
        mo = LOG_RE.match(line)
        if mo:
            push_line(mo.group(1), line)
        else:
            if PYTEST_SECTION_RE.match(line):
                continue
            flush()
            print(line, end='')
            
main()
