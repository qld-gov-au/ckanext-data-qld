#!/usr/bin/env bash
##
# Run tests in CI.
#
set -e


echo "==> Run BDD tests"
ahoy cli "rm test/screenshots/*" || true
ahoy test-bdd || (ahoy logs; exit 1)
