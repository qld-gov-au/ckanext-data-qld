#!/usr/bin/env bash
##
# Run tests in CI.
#
set -e

./test-lint.sh

./test.sh

./test-bdd.sh

