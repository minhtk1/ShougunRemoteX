# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/log.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Import module từ xpra_client
import sys
import os

# Helper function để import module từ third_party.xpra_client
def _import_module(name):
    """Import module từ third_party.xpra_client"""
    import importlib
    # Thử import từ third_party.xpra_client trước
    full_name = f'third_party.xpra_client.{name}'
    try:
        return importlib.import_module(full_name)
    except ImportError:
        # Fallback: import trực tiếp từ third_party
        third_party_path = os.path.join(os.path.dirname(__file__), '..', '..', 'third_party')
        if third_party_path not in sys.path and os.path.exists(third_party_path):
            sys.path.insert(0, third_party_path)
        return importlib.import_module(f'xpra_client.{name}')

# Import và export module
_m = _import_module('log')
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith('_')})