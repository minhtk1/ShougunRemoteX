"""
Ví dụ sử dụng Python service.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shougun_remote.services.factory import ServiceFactory


def example_standalone_service():
    """Ví dụ chạy service độc lập."""
    print("=== Standalone Service Example ===")
    
    # Tạo service
    service = ServiceFactory.create_shougun_service()
    
    # Khởi động service
    print("Starting service...")
    if service.start():
        print("Service started successfully")
        
        # Lấy thông tin service
        info = service.get_info()
        print(f"Service info: {info}")
        
        # Kiểm tra trạng thái
        status = service.get_status()
        print(f"Service status: {status}")
        
        # Chạy một lúc
        import time
        time.sleep(5)
        
        # Dừng service
        print("Stopping service...")
        if service.stop():
            print("Service stopped successfully")
        else:
            print("Failed to stop service")
    else:
        print("Failed to start service")


def example_custom_dependencies():
    """Ví dụ tạo service với custom dependencies."""
    print("\n=== Custom Dependencies Example ===")
    
    from shougun_remote.config.logger import LoguruLogger, LogLevel
    from shougun_remote.config import ConfigManager
    from shougun_remote.repositories import FileRepository
    from shougun_remote.models import Task
    
    # Tạo custom dependencies
    logger = LoguruLogger(LogLevel.DEBUG)
    config_manager = ConfigManager()
    task_repository = FileRepository("data/custom_tasks.json", Task)
    
    # Tạo service với custom dependencies
    service = ServiceFactory.create_with_custom_dependencies(
        logger=logger,
        config_manager=config_manager,
        task_repository=task_repository
    )
    
    # Khởi động service
    if service.start():
        print("Custom service started successfully")
        
        # Dừng service
        service.stop()
        print("Custom service stopped")
    else:
        print("Failed to start custom service")


if __name__ == "__main__":
    try:
        example_standalone_service()
        example_custom_dependencies()
        
        print("\n=== All examples completed successfully ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        sys.exit(1)
