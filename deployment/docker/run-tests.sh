#!/bin/sh
set -e

mkdir -p reports

echo "Starting tests..."
pytest --cov=. --cov-report=xml:reports/coverage.xml --cov-report=term --junitxml=reports/pytest-report.xml tests

echo "Tests done. Reports folder contents:"
ls -la reports
