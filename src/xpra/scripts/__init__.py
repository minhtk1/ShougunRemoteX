# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/scripts/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.scripts to third_party.xpra_client.scripts
import sys
import importlib

# Tạo module xpra.scripts để redirect các import từ xpra.scripts.* sang third_party.xpra_client.scripts.*
class XpraScriptsModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.scripts sang third_party.xpra_client.scripts"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.scripts.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.scripts, thử import từ xpra.scripts gốc
            try:
                original_name = f"xpra.scripts.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.scripts trong sys.modules
if 'xpra.scripts' not in sys.modules:
    sys.modules['xpra.scripts'] = XpraScriptsModuleRedirect('xpra.scripts')

# Import các module cần thiết từ third_party.xpra_client.scripts
from third_party.xpra_client.scripts import config, parsing, main

# Export các module để có thể import trực tiếp
__all__ = ['config', 'parsing', 'main']