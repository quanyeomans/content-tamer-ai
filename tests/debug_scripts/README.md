# Debug Scripts Directory

This directory contains temporary debug and test scripts used during development.

## Contents

- `debug_*.py`: Temporary debug scripts for specific issues
- `test_*.py`: Ad-hoc test scripts for specific functionality
- `debug_results.txt`: Output from debug sessions

## Usage Guidelines

- **Temporary only**: Scripts here are for active debugging sessions
- **Clean up regularly**: Remove scripts after issues are resolved
- **No production use**: These scripts are not part of the main application
- **Document findings**: Update main test suite with any useful patterns found

## Cleanup Policy

Debug scripts should be removed when:
- The issue they were investigating is resolved
- The functionality is covered by proper unit/integration tests
- The debugging session is complete
- Weekly cleanup reviews