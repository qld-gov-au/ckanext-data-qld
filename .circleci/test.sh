#!/usr/bin/env bash
##
# Run tests in CI.
#
set -e

echo "==> Lint code"
ahoy lint

echo "==> Run BDD tests"
ahoy test-bdd

echo "==> Run Unit tests"
ahoy test-unit || (ahoy logs; exit 1)
