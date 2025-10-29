"""
ShougunRemoteX Python Service Package

Dự án Python chuẩn SOLID có thể nhúng vào C# và chạy như background service.
"""

__version__ = "1.0.0"
__author__ = "Shougun Team"
__email__ = "team@shougun.com"

from .core.service_interface import IService
from .core.config_interface import IConfigManager
from .services import ShougunService

__all__ = [
    "IService",
    "IConfigManager", 
    "ShougunService",
]
