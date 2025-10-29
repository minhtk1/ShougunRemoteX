# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/clipboard/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.clipboard to third_party.xpra_client.clipboard
import sys
import importlib

# Tạo module xpra.clipboard để redirect các import từ xpra.clipboard.* sang third_party.xpra_client.clipboard.*
class XpraClipboardModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.clipboard sang third_party.xpra_client.clipboard"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.clipboard.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.clipboard, thử import từ xpra.clipboard gốc
            try:
                original_name = f"xpra.clipboard.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.clipboard trong sys.modules
if 'xpra.clipboard' not in sys.modules:
    sys.modules['xpra.clipboard'] = XpraClipboardModuleRedirect('xpra.clipboard')

# Import các module cần thiết từ third_party.xpra_client.clipboard
# Không có module con nào trong clipboard

# Export các module để có thể import trực tiếp
__all__ = []