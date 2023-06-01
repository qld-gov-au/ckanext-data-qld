#!/usr/bin/env bash
##
# Run tests in CI.
#
set -ex

echo "==> Run BDD tests"
ahoy cli "rm -r test/screenshots || true"
ahoy test-bdd || (ahoy logs; exit 1)
