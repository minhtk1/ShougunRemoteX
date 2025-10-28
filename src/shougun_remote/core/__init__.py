"""
Core interfaces và abstract classes theo nguyên tắc SOLID.
"""

from .service_interface import IService
from .config_interface import IConfigManager
from .logger_interface import ILogger
from .repository_interface import IRepository

__all__ = [
    "IService",
    "IConfigManager",
    "ILogger", 
    "IRepository",
]
