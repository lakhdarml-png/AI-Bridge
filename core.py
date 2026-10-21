#!/usr/bin/env python3
"""Compatibility entry point for the canonical NEO-LOCAL core package."""
import sys
from neo_local import core as _core

if __name__ == "__main__":
    raise SystemExit(_core.main())

# Preserve legacy imports, including tests which configure APP_HOME and DB_PATH.
sys.modules[__name__] = _core
