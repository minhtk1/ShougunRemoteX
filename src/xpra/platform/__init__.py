# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/platform/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.platform to third_party.xpra_client.platform
import sys
import importlib

# Tạo module xpra.platform để redirect các import từ xpra.platform.* sang third_party.xpra_client.platform.*
class XpraPlatformModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.platform sang third_party.xpra_client.platform"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.platform.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.platform, thử import từ xpra.platform gốc
            try:
                original_name = f"xpra.platform.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.platform trong sys.modules
if 'xpra.platform' not in sys.modules:
    sys.modules['xpra.platform'] = XpraPlatformModuleRedirect('xpra.platform')

# Import các module cần thiết từ third_party.xpra_client.platform
from third_party.xpra_client.platform import features, gui, info, paths, win32

# Export các module để có thể import trực tiếp
__all__ = ['features', 'gui', 'info', 'paths', 'win32']