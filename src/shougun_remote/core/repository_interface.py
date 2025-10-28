"""
Repository interface cho data access layer.
Tuân thủ Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    Generic repository interface.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ định nghĩa contract cho data access
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - High-level modules phụ thuộc vào abstraction này
    
    Tuân thủ Open/Closed Principle (OCP):
    - Có thể mở rộng cho các loại entity khác nhau
    """
    
    @abstractmethod
    def create(self, entity: T) -> Optional[T]:
        """
        Tạo entity mới.
        
        Args:
            entity: Entity cần tạo
            
        Returns:
            Optional[T]: Entity đã tạo hoặc None nếu thất bại
        """
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Lấy entity theo ID.
        
        Args:
            entity_id: ID của entity
            
        Returns:
            Optional[T]: Entity hoặc None nếu không tìm thấy
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """
        Lấy tất cả entities.
        
        Returns:
            List[T]: Danh sách tất cả entities
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> bool:
        """
        Cập nhật entity.
        
        Args:
            entity: Entity cần cập nhật
            
        Returns:
            bool: True nếu cập nhật thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Xóa entity theo ID.
        
        Args:
            entity_id: ID của entity cần xóa
            
        Returns:
            bool: True nếu xóa thành công, False nếu thất bại
        """
        pass
    
    @abstractmethod
    def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Tìm entities theo criteria.
        
        Args:
            criteria: Dictionary chứa điều kiện tìm kiếm
            
        Returns:
            List[T]: Danh sách entities thỏa mãn điều kiện
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        Đếm số lượng entities.
        
        Returns:
            int: Số lượng entities
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Kiểm tra entity có tồn tại không.
        
        Args:
            entity_id: ID của entity
            
        Returns:
            bool: True nếu tồn tại, False nếu không
        """
        pass
