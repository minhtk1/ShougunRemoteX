# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/util/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.util to third_party.xpra_client.util
import sys
import importlib

# Tạo module xpra.util để redirect các import từ xpra.util.* sang third_party.xpra_client.util.*
class XpraUtilModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.util sang third_party.xpra_client.util"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.util.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.util, thử import từ xpra.util gốc
            try:
                original_name = f"xpra.util.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.util trong sys.modules
if 'xpra.util' not in sys.modules:
    sys.modules['xpra.util'] = XpraUtilModuleRedirect('xpra.util')

# Import các module cần thiết từ third_party.xpra_client.util
from third_party.xpra_client.util import env, objects, str_fn, parsing, thread, io, system, child_reaper, version

# Export các module để có thể import trực tiếp
__all__ = [
    'env', 'objects', 'str_fn', 'parsing', 'thread', 
    'io', 'system', 'child_reaper', 'version'
]