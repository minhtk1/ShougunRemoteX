"""
Logger interface cho logging system.
Tuân thủ Interface Segregation Principle (ISP).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Các mức độ log."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ILogger(ABC):
    """
    Interface cho logging system.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ định nghĩa contract cho logging
    
    Tuân thủ Interface Segregation Principle (ISP):
    - Interface nhỏ và tập trung vào logging operations
    """
    
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log message ở mức DEBUG.
        
        Args:
            message: Nội dung log
            **kwargs: Các tham số bổ sung
        """
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log message ở mức INFO.
        
        Args:
            message: Nội dung log
            **kwargs: Các tham số bổ sung
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log message ở mức WARNING.
        
        Args:
            message: Nội dung log
            **kwargs: Các tham số bổ sung
        """
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log message ở mức ERROR.
        
        Args:
            message: Nội dung log
            **kwargs: Các tham số bổ sung
        """
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log message ở mức CRITICAL.
        
        Args:
            message: Nội dung log
            **kwargs: Các tham số bổ sung
        """
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """
        Đặt mức độ log.
        
        Args:
            level: Mức độ log mới
        """
        pass
    
    @abstractmethod
    def get_level(self) -> LogLevel:
        """
        Lấy mức độ log hiện tại.
        
        Returns:
            LogLevel: Mức độ log hiện tại
        """
        pass
