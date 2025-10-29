# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/keyboard/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.keyboard to third_party.xpra_client.keyboard
import sys
import importlib

# Tạo module xpra.keyboard để redirect các import từ xpra.keyboard.* sang third_party.xpra_client.keyboard.*
class XpraKeyboardModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.keyboard sang third_party.xpra_client.keyboard"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.keyboard.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.keyboard, thử import từ xpra.keyboard gốc
            try:
                original_name = f"xpra.keyboard.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.keyboard trong sys.modules
if 'xpra.keyboard' not in sys.modules:
    sys.modules['xpra.keyboard'] = XpraKeyboardModuleRedirect('xpra.keyboard')

# Import các module cần thiết từ third_party.xpra_client.keyboard
from third_party.xpra_client.keyboard import common

# Export các module để có thể import trực tiếp
__all__ = ['common']