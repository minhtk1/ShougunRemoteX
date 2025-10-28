"""
Repository implementations.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
import json
from pathlib import Path
from ..core.repository_interface import IRepository
from ..models import Task

T = TypeVar('T')


class FileRepository(IRepository[T], Generic[T]):
    """
    File-based repository implementation.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ quản lý data persistence
    
    Tuân thủ Open/Closed Principle (OCP):
    - Mở để mở rộng các loại entity khác nhau
    """
    
    def __init__(self, file_path: str, entity_class: type):
        self._file_path = Path(file_path)
        self._entity_class = entity_class
        self._data: Dict[str, T] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Tải dữ liệu từ file."""
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self._entity_class, 'from_dict'):
                            self._data[key] = self._entity_class.from_dict(value)
                        else:
                            self._data[key] = value
            except Exception:
                self._data = {}
        else:
            self._data = {}
    
    def _save_data(self) -> bool:
        """Lưu dữ liệu ra file."""
        try:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for key, entity in self._data.items():
                if hasattr(entity, 'to_dict'):
                    data[key] = entity.to_dict()
                else:
                    data[key] = entity
            
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception:
            return False
    
    def create(self, entity: T) -> Optional[T]:
        """Tạo entity mới."""
        if hasattr(entity, 'id'):
            entity_id = str(entity.id)
            self._data[entity_id] = entity
            if self._save_data():
                return entity
        return None
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Lấy entity theo ID."""
        return self._data.get(entity_id)
    
    def get_all(self) -> List[T]:
        """Lấy tất cả entities."""
        return list(self._data.values())
    
    def update(self, entity: T) -> bool:
        """Cập nhật entity."""
        if hasattr(entity, 'id'):
            entity_id = str(entity.id)
            if entity_id in self._data:
                self._data[entity_id] = entity
                return self._save_data()
        return False
    
    def delete(self, entity_id: str) -> bool:
        """Xóa entity theo ID."""
        if entity_id in self._data:
            del self._data[entity_id]
            return self._save_data()
        return False
    
    def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """Tìm entities theo criteria."""
        results = []
        for entity in self._data.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(entity, key) or getattr(entity, key) != value:
                    match = False
                    break
            if match:
                results.append(entity)
        return results
    
    def count(self) -> int:
        """Đếm số lượng entities."""
        return len(self._data)
    
    def exists(self, entity_id: str) -> bool:
        """Kiểm tra entity có tồn tại không."""
        return entity_id in self._data
