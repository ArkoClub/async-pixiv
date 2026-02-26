"""Compatibility shims for optional dependencies."""

try:
    from orjson import loads as json_loads
except ImportError:
    from json import loads as json_loads

try:
    import regex as re
except ImportError:
    import re

__all__ = ("json_loads", "re")
