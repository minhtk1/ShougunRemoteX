# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/client/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.client to third_party.xpra_client.client
import sys
import importlib

# Tạo module xpra.client để redirect các import từ xpra.client.* sang third_party.xpra_client.client.*
class XpraClientModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.client sang third_party.xpra_client.client"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.client.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.client, thử import từ xpra.client gốc
            try:
                original_name = f"xpra.client.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.client trong sys.modules
if 'xpra.client' not in sys.modules:
    sys.modules['xpra.client'] = XpraClientModuleRedirect('xpra.client')

# Import các module cần thiết từ third_party.xpra_client.client
from third_party.xpra_client.client import base, gtk3, gui, mixins

# Export các module để có thể import trực tiếp
__all__ = ['base', 'gtk3', 'gui', 'mixins']