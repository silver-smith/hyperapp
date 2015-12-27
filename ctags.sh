#!/bin/sh

find -name '*.py' | xargs etags -o TAGS
