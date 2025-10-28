"""
Logger implementation sử dụng loguru.
"""

from typing import Any, Optional
from loguru import logger as loguru_logger
from ..core.logger_interface import ILogger, LogLevel


class LoguruLogger(ILogger):
    """
    Implementation của ILogger sử dụng loguru.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ xử lý logging
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - Implement interface ILogger
    """
    
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self._level = level
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Thiết lập logger."""
        loguru_logger.remove()  # Xóa default handler
        
        # Thêm console handler
        loguru_logger.add(
            sink=lambda msg: print(msg, end=""),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self._level.value,
            colorize=True,
        )
        
        # Thêm file handler
        loguru_logger.add(
            "logs/shougun_service.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self._level.value,
        )
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log message ở mức DEBUG."""
        loguru_logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log message ở mức INFO."""
        loguru_logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log message ở mức WARNING."""
        loguru_logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log message ở mức ERROR."""
        loguru_logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log message ở mức CRITICAL."""
        loguru_logger.critical(message, **kwargs)
    
    def set_level(self, level: LogLevel) -> None:
        """Đặt mức độ log."""
        self._level = level
        self._setup_logger()
    
    def get_level(self) -> LogLevel:
        """Lấy mức độ log hiện tại."""
        return self._level
