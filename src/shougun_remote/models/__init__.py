"""
Data models cho dự án.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Trạng thái của task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    Model cho Task.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ chứa dữ liệu của task
    """
    id: str
    name: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi thành dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Tạo Task từ dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ServiceInfo:
    """
    Model cho thông tin service.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ chứa thông tin về service
    """
    name: str
    version: str
    status: str
    uptime: float
    memory_usage: float
    cpu_usage: float
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi thành dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "uptime": self.uptime,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "created_at": self.created_at.isoformat(),
        }
