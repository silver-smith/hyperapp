#!/bin/sh

cd $(dirname $0)
find -name '*.py' | xargs etags -o TAGS
