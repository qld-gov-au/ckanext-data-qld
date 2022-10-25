#!/usr/bin/env bash
##
# Run tests in CI.
#
set -e

./test-lint.sh

./test-bdd.sh

./test.sh
