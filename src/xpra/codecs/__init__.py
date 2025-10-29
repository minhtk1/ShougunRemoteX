# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/codecs/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.codecs to third_party.xpra_client.codecs
import sys
import importlib

# Tạo module xpra.codecs để redirect các import từ xpra.codecs.* sang third_party.xpra_client.codecs.*
class XpraCodecsModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.codecs sang third_party.xpra_client.codecs"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.codecs.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.codecs, thử import từ xpra.codecs gốc
            try:
                original_name = f"xpra.codecs.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.codecs trong sys.modules
if 'xpra.codecs' not in sys.modules:
    sys.modules['xpra.codecs'] = XpraCodecsModuleRedirect('xpra.codecs')

# Import các module cần thiết từ third_party.xpra_client.codecs
from third_party.xpra_client.codecs import loader, pillow, argb

# Export các module để có thể import trực tiếp
__all__ = ['loader', 'pillow', 'argb']