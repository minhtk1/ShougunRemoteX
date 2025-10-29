# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/net/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra.net to third_party.xpra_client.net
import sys
import importlib

# Tạo module xpra.net để redirect các import từ xpra.net.* sang third_party.xpra_client.net.*
class XpraNetModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.net sang third_party.xpra_client.net"""
    
    def __init__(self, name):
        self.name = name
        self._redirected_modules = {}
    
    def __getattr__(self, name):
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Tạo module redirect mới
        redirected_name = f"third_party.xpra_client.net.{name}"
        try:
            module = importlib.import_module(redirected_name)
            self._redirected_modules[name] = module
            return module
        except ImportError:
            # Nếu không tìm thấy trong third_party.xpra_client.net, thử import từ xpra.net gốc
            try:
                original_name = f"xpra.net.{name}"
                module = importlib.import_module(original_name)
                self._redirected_modules[name] = module
                return module
            except ImportError:
                raise AttributeError(f"module '{self.name}' has no attribute '{name}'")

# Thay thế module xpra.net trong sys.modules
if 'xpra.net' not in sys.modules:
    sys.modules['xpra.net'] = XpraNetModuleRedirect('xpra.net')

# Import các module cần thiết từ third_party.xpra_client.net
from third_party.xpra_client.net import common, bytestreams, socket_util, compression, packet_encoding

# Export các module để có thể import trực tiếp
__all__ = ['common', 'bytestreams', 'socket_util', 'compression', 'packet_encoding']