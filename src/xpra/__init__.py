# Code copied from xpra-client under GNU General Public License v2.0
# Original source: xpra-client/xpra/__init__.py
# License: GNU General Public License v2.0
# This file is part of ShougunRemoteX-Python project

# Redirect imports from xpra to third_party.xpra_client
import sys
import os
import importlib
import re

# Import __version__ và __version_info__ từ third_party.xpra_client ngay đầu file
# để tránh circular import khi các module khác cần truy cập xpra.__version__
# Đọc trực tiếp từ file để tránh trigger import chain
try:
    # Tìm đường dẫn đến third_party/xpra_client/__init__.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    third_party_init_path = os.path.join(current_dir, '..', '..', 'third_party', 'xpra_client', '__init__.py')
    third_party_init_path = os.path.normpath(third_party_init_path)
    
    # Đọc file và parse __version__ và __version_info__
    if os.path.exists(third_party_init_path):
        with open(third_party_init_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse __version__ = "6.3.4"
            version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            version_info_match = re.search(r'__version_info__\s*=\s*\(([^)]+)\)', content)
            
            if version_match:
                __version__ = version_match.group(1)
            else:
                __version__ = '6.3.4'
                
            if version_info_match:
                # Parse tuple như (6, 3, 4)
                version_info_str = version_info_match.group(1)
                version_info_tuple = tuple(int(x.strip()) for x in version_info_str.split(','))
                __version_info__ = version_info_tuple
            else:
                __version_info__ = (6, 3, 4)
    else:
        # Fallback: giá trị mặc định
        __version__ = '6.3.4'
        __version_info__ = (6, 3, 4)
except Exception:
    # Giá trị mặc định nếu không thể đọc file
    __version__ = '6.3.4'
    __version_info__ = (6, 3, 4)

def _import_xpra_module(module_name: str):
    """
    Import module từ third_party.xpra_client với fallback handling
    
    Args:
        module_name: Tên module cần import (vd: 'common', 'util.env')
    
    Returns:
        Imported module
    """
    # Thử import từ third_party.xpra_client
    full_name = f'third_party.xpra_client.{module_name}'
    try:
        return importlib.import_module(full_name)
    except ImportError:
        # Fallback: thử import trực tiếp từ third_party
        try:
            # Thêm third_party vào path nếu chưa có
            third_party_path = os.path.join(os.path.dirname(__file__), '..', '..', 'third_party')
            if third_party_path not in sys.path and os.path.exists(third_party_path):
                sys.path.insert(0, third_party_path)
            
            # Import từ xpra_client trong third_party
            fallback_name = f'xpra_client.{module_name}'
            return importlib.import_module(fallback_name)
        except ImportError:
            raise ImportError(f"Cannot import module '{module_name}' from third_party.xpra_client or xpra_client")


# Tạo module redirect để chuyển hướng import
class XpraModuleRedirect:
    """Module redirect để chuyển hướng import từ xpra.* sang third_party.xpra_client.*"""
    
    def __init__(self, name, version, version_info):
        self.name = name
        self._redirected_modules = {}
        # Lưu version attributes để tránh circular import
        self.__version__ = version
        self.__version_info__ = version_info
    
    def __getattr__(self, name):
        # Trả về __version__ và __version_info__ nếu được yêu cầu
        if name == '__version__':
            return self.__version__
        if name == '__version_info__':
            return self.__version_info__
        
        # Nếu đã có module được cache, trả về
        if name in self._redirected_modules:
            return self._redirected_modules[name]
        
        # Import module
        try:
            module = _import_xpra_module(name)
            self._redirected_modules[name] = module
            return module
        except ImportError as e:
            raise AttributeError(f"module '{self.name}' has no attribute '{name}': {e}")

# Thay thế module xpra trong sys.modules
if 'xpra' not in sys.modules:
    sys.modules['xpra'] = XpraModuleRedirect('xpra', __version__, __version_info__)

# Import và export các module chính
try:
    from third_party.xpra_client import common, util, net, scripts, platform, gtk, client, clipboard, codecs, keyboard, log, os_util, exit_codes
    __all__ = [
        'common', 'util', 'net', 'scripts', 'platform', 'gtk', 
        'client', 'clipboard', 'codecs', 'keyboard', 'log', 'os_util', 'exit_codes'
    ]
except ImportError:
    # Nếu không thể import, __all__ sẽ rỗng
    __all__ = []