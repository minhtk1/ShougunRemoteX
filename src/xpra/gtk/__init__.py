# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/gtk/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.gtk to third_party.xpra_client.gtk
import sys
import importlib

# Tạo module xpra.gtk để redirect các import từ xpra.gtk.* sang third_party.xpra_client.gtk.*
class XpraGtkModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.gtk sang third_party.xpra_client.gtk"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.gtk.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.gtk, thử import từ xpra.gtk gốc
            try:
                original_name = f"xpra.gtk.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.gtk trong sys.modules
if 'xpra.gtk' not in sys.modules:
    sys.modules['xpra.gtk'] = XpraGtkModuleRedirect('xpra.gtk')

# Import các module cần thiết từ third_party.xpra_client.gtk
from third_party.xpra_client.gtk import util, widget, window, info, signals, gobject, css_overrides, cursors, pixbuf, versions

# Export các module để có thể import trực tiếp
__all__ = ['util', 'widget', 'window', 'info', 'signals', 'gobject', 'css_overrides', 'cursors', 'pixbuf', 'versions']