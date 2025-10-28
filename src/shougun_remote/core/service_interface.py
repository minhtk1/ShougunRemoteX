"""
Service interface định nghĩa contract cho tất cả services.
Tuân thủ Interface Segregation Principle (ISP).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ServiceStatus(Enum):
    """Trạng thái của service."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class IService(ABC):
    """
    Interface cho tất cả services.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ định nghĩa contract cho service lifecycle
    
    Tuân thủ Interface Segregation Principle (ISP):
    - Interface nhỏ và tập trung vào service operations
    """
    
    @abstractmethod
    def start(self) -> bool:
        """
        Khởi động service.
        
        Returns:
            bool: True nếu khởi động thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Dừng service.
        
        Returns:
            bool: True nếu dừng thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def restart(self) -> bool:
        """
        Khởi động lại service.
        
        Returns:
            bool: True nếu khởi động lại thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """
        Lấy trạng thái hiện tại của service.
        
        Returns:
            ServiceStatus: Trạng thái hiện tại
        """
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin về service.
        
        Returns:
            Dict[str, Any]: Thông tin service
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """
        Kiểm tra service có đang chạy không.
        
        Returns:
            bool: True nếu đang chạy, False nếu không
        """
        pass
