#!/bin/sh
# The universal components provide
# a set of platform specific compatibility modules
# that all need to have the exact same qmldir file.
# This script copies the main qmldir to the all the
# platform specific modules, so they don't have to be
# kept in sync manually.
#
#
# Note: If you add a new compatibility module,
# add it here.

cp main_qmldir controls/UC/qmldir
cp main_qmldir silica/UC/qmldir
cp main_qmldir glacier/UC/qmldir
cp main_qmldir ubuntu/UC/qmldir
