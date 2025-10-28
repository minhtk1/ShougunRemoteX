"""
Configuration interface cho quản lý cấu hình.
Tuân thủ Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from pathlib import Path


class IConfigManager(ABC):
    """
    Interface cho quản lý cấu hình.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ quản lý cấu hình
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - High-level modules phụ thuộc vào abstraction này
    """
    
    @abstractmethod
    def load_config(self, config_path: Union[str, Path]) -> bool:
        """
        Tải cấu hình từ file.
        
        Args:
            config_path: Đường dẫn đến file cấu hình
            
        Returns:
            bool: True nếu tải thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def save_config(self, config_path: Union[str, Path]) -> bool:
        """
        Lưu cấu hình ra file.
        
        Args:
            config_path: Đường dẫn đến file cấu hình
            
        Returns:
            bool: True nếu lưu thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị cấu hình theo key.
        
        Args:
            key: Key cấu hình
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Any: Giá trị cấu hình
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """
        Đặt giá trị cấu hình.
        
        Args:
            key: Key cấu hình
            value: Giá trị cấu hình
            
        Returns:
            bool: True nếu đặt thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Lấy toàn bộ section cấu hình.
        
        Args:
            section: Tên section
            
        Returns:
            Dict[str, Any]: Dictionary chứa cấu hình section
        """
        pass
    
    @abstractmethod
    def has_key(self, key: str) -> bool:
        """
        Kiểm tra key có tồn tại không.
        
        Args:
            key: Key cần kiểm tra
            
        Returns:
            bool: True nếu tồn tại, False nếu không
        """
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        Lấy toàn bộ cấu hình.
        
        Returns:
            Dict[str, Any]: Dictionary chứa toàn bộ cấu hình
        """
        pass
