"""
Service implementations theo nguyên tắc SOLID.
"""

import time
import threading
import psutil
from typing import Any, Dict, Optional
from datetime import datetime

from ..core.service_interface import IService, ServiceStatus
from ..core.logger_interface import ILogger
from ..core.config_interface import IConfigManager
from ..models import Task, ServiceInfo, TaskStatus
from ..repositories import FileRepository
from ..monitors import FolderMonitor, JsonReader


class TaskService:
    """
    Service quản lý tasks.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ quản lý tasks
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - Phụ thuộc vào abstractions (ILogger, IRepository)
    """
    
    def __init__(self, logger: ILogger, task_repository: FileRepository[Task]):
        self._logger = logger
        self._task_repository = task_repository
    
    def create_task(self, name: str, description: Optional[str] = None) -> Optional[Task]:
        """Tạo task mới."""
        try:
            task_id = f"task_{int(time.time())}"
            task = Task(
                id=task_id,
                name=name,
                description=description
            )
            
            result = self._task_repository.create(task)
            if result:
                self._logger.info(f"Created task: {task_id}")
                return result
            else:
                self._logger.error(f"Failed to create task: {task_id}")
                return None
        except Exception as e:
            self._logger.error(f"Error creating task: {e}")
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Lấy task theo ID."""
        return self._task_repository.get_by_id(task_id)
    
    def get_all_tasks(self) -> list[Task]:
        """Lấy tất cả tasks."""
        return self._task_repository.get_all()
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Cập nhật trạng thái task."""
        try:
            task = self._task_repository.get_by_id(task_id)
            if task:
                task.status = status
                task.updated_at = datetime.now()
                return self._task_repository.update(task)
            return False
        except Exception as e:
            self._logger.error(f"Error updating task status: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Xóa task."""
        try:
            result = self._task_repository.delete(task_id)
            if result:
                self._logger.info(f"Deleted task: {task_id}")
            return result
        except Exception as e:
            self._logger.error(f"Error deleting task: {e}")
            return False


class ShougunService(IService):
    """
    Main service implementation.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ quản lý service lifecycle
    
    Tuân thủ Dependency Inversion Principle (DIP):
    - Phụ thuộc vào abstractions
    """
    
    def __init__(
        self,
        logger: ILogger,
        config_manager: IConfigManager,
        task_service: TaskService
    ):
        self._logger = logger
        self._config_manager = config_manager
        self._task_service = task_service
        
        self._status = ServiceStatus.STOPPED
        self._start_time: Optional[datetime] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Folder monitoring components
        self._json_reader = JsonReader()
        self._folder_monitor: Optional[FolderMonitor] = None
    
    def start(self) -> bool:
        """Khởi động service."""
        try:
            if self._status == ServiceStatus.RUNNING:
                self._logger.warning("Service is already running")
                return True
            
            self._status = ServiceStatus.STARTING
            self._logger.info("Starting Shougun Service...")
            
            # Load configuration
            if not self._config_manager.load_config("config/service.json"):
                self._logger.warning("Failed to load config, using defaults")
            
            # Initialize folder monitoring
            self._init_folder_monitoring()
            
            # Start worker thread
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            
            self._start_time = datetime.now()
            self._status = ServiceStatus.RUNNING
            
            self._logger.info("Shougun Service started successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    def stop(self) -> bool:
        """Dừng service."""
        try:
            if self._status == ServiceStatus.STOPPED:
                self._logger.warning("Service is already stopped")
                return True
            
            self._status = ServiceStatus.STOPPING
            self._logger.info("Stopping Shougun Service...")
            
            # Stop folder monitoring
            self._stop_folder_monitoring()
            
            # Signal worker thread to stop
            self._stop_event.set()
            
            # Wait for worker thread to finish
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=5.0)
            
            self._status = ServiceStatus.STOPPED
            self._logger.info("Shougun Service stopped successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to stop service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    def restart(self) -> bool:
        """Khởi động lại service."""
        self._logger.info("Restarting Shougun Service...")
        if self.stop():
            return self.start()
        return False
    
    def get_status(self) -> ServiceStatus:
        """Lấy trạng thái hiện tại của service."""
        return self._status
    
    def get_info(self) -> Dict[str, Any]:
        """Lấy thông tin về service."""
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "name": "ShougunService",
            "version": "1.0.0",
            "status": self._status.value,
            "uptime": uptime,
            "memory_usage": memory_info.rss / 1024 / 1024,  # MB
            "cpu_usage": process.cpu_percent(),
            "pid": process.pid,
            "thread_count": process.num_threads(),
        }
    
    def is_running(self) -> bool:
        """Kiểm tra service có đang chạy không."""
        return self._status == ServiceStatus.RUNNING
    
    def _worker_loop(self) -> None:
        """Worker loop chạy trong background."""
        self._logger.info("Worker thread started")
        
        while not self._stop_event.is_set():
            try:
                # Do background work here
                self._process_tasks()
                
                # Sleep for a short interval
                self._stop_event.wait(1.0)
                
            except Exception as e:
                self._logger.error(f"Error in worker loop: {e}")
                time.sleep(1.0)
        
        self._logger.info("Worker thread stopped")
    
    def _process_tasks(self) -> None:
        """Xử lý các tasks."""
        try:
            # Get pending tasks
            pending_tasks = self._task_service._task_repository.find_by({
                "status": TaskStatus.PENDING
            })
            
            for task in pending_tasks:
                self._logger.debug(f"Processing task: {task.id}")
                # Update task status to running
                self._task_service.update_task_status(task.id, TaskStatus.RUNNING)
                
                # Simulate task processing
                time.sleep(0.1)
                
                # Mark task as completed
                self._task_service.update_task_status(task.id, TaskStatus.COMPLETED)
                
        except Exception as e:
            self._logger.error(f"Error processing tasks: {e}")
    
    def _init_folder_monitoring(self) -> None:
        """Khởi tạo folder monitoring."""
        try:
            # Tạo callback function để xử lý file JSON
            def json_callback(file_path: str, data: Dict[str, Any]) -> None:
                """Callback được gọi khi có file JSON thay đổi."""
                self._logger.info(f"Nhận được file JSON mới: {file_path}")
                
                # Xử lý dữ liệu JSON
                if self._json_reader.process_json_data(file_path, data):
                    self._logger.info(f"Đã xử lý thành công file JSON: {file_path}")
                else:
                    self._logger.warning(f"Không thể xử lý file JSON: {file_path}")
            
            # Tạo folder monitor
            self._folder_monitor = FolderMonitor(json_callback)
            
            # Bắt đầu theo dõi
            if self._folder_monitor.start_monitoring():
                self._logger.info(f"Bắt đầu theo dõi folder: {self._folder_monitor.get_folder_path()}")
                
                # Quét các file JSON hiện có
                self._folder_monitor.scan_existing_files()
            else:
                self._logger.error("Không thể bắt đầu theo dõi folder")
                
        except Exception as e:
            self._logger.error(f"Lỗi khởi tạo folder monitoring: {e}")
    
    def _stop_folder_monitoring(self) -> None:
        """Dừng folder monitoring."""
        try:
            if self._folder_monitor:
                self._folder_monitor.stop_monitoring()
                self._logger.info("Đã dừng theo dõi folder")
        except Exception as e:
            self._logger.error(f"Lỗi khi dừng folder monitoring: {e}")
    
    def get_monitored_folder_path(self) -> Optional[str]:
        """
        Lấy đường dẫn folder đang được theo dõi.
        
        Returns:
            Optional[str]: Đường dẫn folder hoặc None nếu chưa khởi tạo
        """
        if self._folder_monitor:
            return self._folder_monitor.get_folder_path()
        return None
    
    def is_folder_monitoring_active(self) -> bool:
        """
        Kiểm tra xem folder monitoring có đang hoạt động không.
        
        Returns:
            bool: True nếu đang hoạt động, False nếu không
        """
        if self._folder_monitor:
            return self._folder_monitor.is_running()
        return False
