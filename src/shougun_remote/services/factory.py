"""
Dependency injection container và factory.
"""

from typing import Any, Dict, Type, TypeVar, Optional
from ..core.service_interface import IService
from ..core.logger_interface import ILogger, LogLevel
from ..core.config_interface import IConfigManager
from ..config import ConfigManager
from ..config.logger import LoguruLogger
from ..repositories import FileRepository
from . import ShougunService, TaskService
from ..models import Task

T = TypeVar('T')


class DIContainer:
    """
    Dependency Injection Container.
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - Quản lý dependencies và inversion of control
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Đăng ký singleton service."""
        self._services[interface] = implementation
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Đăng ký transient service."""
        self._services[interface] = implementation
    
    def get(self, interface: Type[T]) -> T:
        """Lấy service instance."""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")
        
        implementation = self._services[interface]
        instance = implementation()
        
        # Check if it's a singleton
        if interface in self._services:
            self._singletons[interface] = instance
        
        return instance
    
    def get_instance(self, interface: Type[T], instance: T) -> None:
        """Đăng ký instance có sẵn."""
        self._singletons[interface] = instance


class ServiceFactory:
    """
    Factory để tạo services với dependency injection.
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - Tạo services với proper dependencies
    """
    
    @staticmethod
    def create_shougun_service() -> IService:
        """Tạo ShougunService với dependencies."""
        container = DIContainer()
        
        # Register core services
        container.register_singleton(ILogger, lambda: LoguruLogger(LogLevel.INFO))
        container.register_singleton(IConfigManager, ConfigManager)
        container.register_singleton(FileRepository[Task], lambda: FileRepository("data/tasks.json", Task))
        
        # Get dependencies
        logger = container.get(ILogger)
        config_manager = container.get(IConfigManager)
        task_repository = container.get(FileRepository[Task])
        
        # Create task service
        task_service = TaskService(logger, task_repository)
        
        # Create main service
        service = ShougunService(logger, config_manager, task_service)
        
        return service
    
    @staticmethod
    def create_with_custom_dependencies(
        logger: Optional[ILogger] = None,
        config_manager: Optional[IConfigManager] = None,
        task_repository: Optional[FileRepository[Task]] = None
    ) -> IService:
        """Tạo service với custom dependencies."""
        # Use provided dependencies or create defaults
        if logger is None:
            logger = LoguruLogger(LogLevel.INFO)
        
        if config_manager is None:
            config_manager = ConfigManager()
        
        if task_repository is None:
            task_repository = FileRepository("data/tasks.json", Task)
        
        # Create task service
        task_service = TaskService(logger, task_repository)
        
        # Create main service
        service = ShougunService(logger, config_manager, task_service)
        
        return service
