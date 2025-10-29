"""
Test cases cho dự án.
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shougun_remote.core.service_interface import ServiceStatus
from shougun_remote.services.factory import ServiceFactory
from shougun_remote.config import ConfigManager
from shougun_remote.config.logger import LoguruLogger, LogLevel
from shougun_remote.repositories import FileRepository
from shougun_remote.models import Task, TaskStatus
# CSharpBridge module không tồn tại - đã được xóa khỏi project


class TestConfigManager:
    """Test cases cho ConfigManager."""
    
    def test_load_config_json(self):
        """Test load JSON config."""
        config_manager = ConfigManager()
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "value", "nested": {"key": "value"}}, f)
            temp_path = f.name
        
        try:
            assert config_manager.load_config(temp_path)
            assert config_manager.get("test") == "value"
            assert config_manager.get("nested.key") == "value"
        finally:
            Path(temp_path).unlink()
    
    def test_save_config_json(self):
        """Test save JSON config."""
        config_manager = ConfigManager()
        config_manager.set("test", "value")
        config_manager.set("nested.key", "value")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            assert config_manager.save_config(temp_path)
            
            # Load and verify
            new_config = ConfigManager()
            assert new_config.load_config(temp_path)
            assert new_config.get("test") == "value"
            assert new_config.get("nested.key") == "value"
        finally:
            Path(temp_path).unlink()


class TestFileRepository:
    """Test cases cho FileRepository."""
    
    def test_create_and_get_task(self):
        """Test create and get task."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            repository = FileRepository(temp_path, Task)
            
            # Create task
            task = Task(id="test1", name="Test Task", description="Test Description")
            created_task = repository.create(task)
            
            assert created_task is not None
            assert created_task.id == "test1"
            
            # Get task
            retrieved_task = repository.get_by_id("test1")
            assert retrieved_task is not None
            assert retrieved_task.name == "Test Task"
            assert retrieved_task.description == "Test Description"
            
        finally:
            Path(temp_path).unlink()
    
    def test_update_task(self):
        """Test update task."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            repository = FileRepository(temp_path, Task)
            
            # Create task
            task = Task(id="test1", name="Test Task")
            repository.create(task)
            
            # Update task
            task.name = "Updated Task"
            task.status = TaskStatus.COMPLETED
            assert repository.update(task)
            
            # Verify update
            updated_task = repository.get_by_id("test1")
            assert updated_task.name == "Updated Task"
            assert updated_task.status == TaskStatus.COMPLETED
            
        finally:
            Path(temp_path).unlink()
    
    def test_delete_task(self):
        """Test delete task."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            repository = FileRepository(temp_path, Task)
            
            # Create task
            task = Task(id="test1", name="Test Task")
            repository.create(task)
            
            # Verify task exists
            assert repository.exists("test1")
            
            # Delete task
            assert repository.delete("test1")
            
            # Verify task deleted
            assert not repository.exists("test1")
            assert repository.get_by_id("test1") is None
            
        finally:
            Path(temp_path).unlink()


class TestShougunService:
    """Test cases cho ShougunService."""
    
    def test_service_lifecycle(self):
        """Test service start/stop lifecycle."""
        service = ServiceFactory.create_shougun_service()
        
        # Initial status should be stopped
        assert service.get_status() == ServiceStatus.STOPPED
        assert not service.is_running()
        
        # Start service
        assert service.start()
        assert service.get_status() == ServiceStatus.RUNNING
        assert service.is_running()
        
        # Get service info
        info = service.get_info()
        assert info["name"] == "ShougunService"
        assert info["version"] == "1.0.0"
        assert info["status"] == ServiceStatus.RUNNING.value
        
        # Stop service
        assert service.stop()
        assert service.get_status() == ServiceStatus.STOPPED
        assert not service.is_running()
    
    def test_service_restart(self):
        """Test service restart."""
        service = ServiceFactory.create_shougun_service()
        
        # Start service
        assert service.start()
        assert service.is_running()
        
        # Restart service
        assert service.restart()
        assert service.is_running()
        
        # Stop service
        assert service.stop()


# Các test cases cho CSharpBridge đã được xóa vì module không tồn tại


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
