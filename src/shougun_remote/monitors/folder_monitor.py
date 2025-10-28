"""
Folder Monitor - Theo dõi thay đổi trong folder

Class này theo dõi folder ShougunIsConnected và phát hiện khi có file JSON mới hoặc thay đổi.
"""

import os
import time
import threading
from pathlib import Path
from typing import Callable, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
from loguru import logger


class ShougunFolderHandler(FileSystemEventHandler):
    """Handler để xử lý sự kiện thay đổi file trong folder ShougunIsConnected."""
    
    def __init__(self, callback: Callable[[str, dict], None]):
        """
        Khởi tạo handler.
        
        Args:
            callback: Hàm callback được gọi khi có file JSON thay đổi
        """
        self.callback = callback
        self.json_files = set()  # Set để theo dõi các file JSON đã xử lý
        
    def on_created(self, event):
        """Xử lý khi có file mới được tạo."""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._process_json_file(event.src_path)
    
    def on_modified(self, event):
        """Xử lý khi file được sửa đổi."""
        if not event.is_directory and event.src_path.endswith('.json'):
            self._process_json_file(event.src_path)
    
    def _process_json_file(self, file_path: str):
        """
        Xử lý file JSON.
        
        Args:
            file_path: Đường dẫn đến file JSON
        """
        try:
            # Đọc nội dung file JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Gọi callback với đường dẫn file và dữ liệu JSON
            self.callback(file_path, data)
            
            # Thêm vào danh sách đã xử lý
            self.json_files.add(file_path)
            
            logger.info(f"Đã xử lý file JSON: {file_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi parse JSON từ file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Lỗi xử lý file {file_path}: {e}")


class FolderMonitor:
    """Class theo dõi folder ShougunIsConnected."""
    
    def __init__(self, callback: Callable[[str, dict], None]):
        """
        Khởi tạo folder monitor.
        
        Args:
            callback: Hàm callback được gọi khi có file JSON thay đổi
        """
        self.callback = callback
        self.observer = None
        self.monitor_thread = None
        self.is_monitoring = False
        self.target_folder = self._get_shougun_folder_path()
        
    def _get_shougun_folder_path(self) -> str:
        """
        Lấy đường dẫn đến folder ShougunIsConnected.
        Xử lý trường hợp folder Users có thể là tiếng Nhật.
        
        Returns:
            str: Đường dẫn đến folder ShougunIsConnected
        """
        try:
            # Thử các cách khác nhau để lấy đường dẫn Public
            possible_paths = [
                r"C:\Users\Public\ShougunIsConnected",
                r"C:\ユーザー\Public\ShougunIsConnected",  # Tiếng Nhật
                r"C:\Users\公用\ShougunIsConnected",  # Tiếng Trung
                os.path.expanduser(r"~\..\Public\ShougunIsConnected"),  # Relative path
            ]
            
            for path in possible_paths:
                if os.path.exists(os.path.dirname(path)):
                    # Tạo folder nếu chưa tồn tại
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"Sử dụng đường dẫn: {path}")
                    return path
            
            # Fallback: tạo trong thư mục hiện tại
            fallback_path = os.path.join(os.getcwd(), "ShougunIsConnected")
            os.makedirs(fallback_path, exist_ok=True)
            logger.warning(f"Không tìm thấy folder Public, sử dụng: {fallback_path}")
            return fallback_path
            
        except Exception as e:
            logger.error(f"Lỗi khi tạo đường dẫn folder: {e}")
            # Fallback cuối cùng
            fallback_path = os.path.join(os.getcwd(), "ShougunIsConnected")
            os.makedirs(fallback_path, exist_ok=True)
            return fallback_path
    
    def start_monitoring(self) -> bool:
        """
        Bắt đầu theo dõi folder.
        
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            if self.is_monitoring:
                logger.warning("Folder monitor đã đang chạy")
                return True
            
            # Tạo observer và handler
            self.observer = Observer()
            handler = ShougunFolderHandler(self.callback)
            
            # Bắt đầu theo dõi
            self.observer.schedule(handler, self.target_folder, recursive=False)
            self.observer.start()
            
            self.is_monitoring = True
            
            logger.info(f"Bắt đầu theo dõi folder: {self.target_folder}")
            return True
            
        except Exception as e:
            logger.error(f"Lỗi khi bắt đầu theo dõi folder: {e}")
            return False
    
    def stop_monitoring(self):
        """Dừng theo dõi folder."""
        try:
            if self.observer and self.is_monitoring:
                self.observer.stop()
                self.observer.join()
                self.is_monitoring = False
                logger.info("Đã dừng theo dõi folder")
        except Exception as e:
            logger.error(f"Lỗi khi dừng theo dõi folder: {e}")
    
    def get_folder_path(self) -> str:
        """
        Lấy đường dẫn folder đang được theo dõi.
        
        Returns:
            str: Đường dẫn folder
        """
        return self.target_folder
    
    def scan_existing_files(self):
        """
        Quét và xử lý các file JSON đã tồn tại trong folder.
        """
        try:
            if not os.path.exists(self.target_folder):
                logger.warning(f"Folder không tồn tại: {self.target_folder}")
                return
            
            # Quét tất cả file JSON trong folder
            for filename in os.listdir(self.target_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.target_folder, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        self.callback(file_path, data)
                        logger.info(f"Đã xử lý file JSON hiện có: {file_path}")
                    except Exception as e:
                        logger.error(f"Lỗi xử lý file hiện có {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Lỗi khi quét file hiện có: {e}")
    
    def is_running(self) -> bool:
        """
        Kiểm tra xem monitor có đang chạy không.
        
        Returns:
            bool: True nếu đang chạy, False nếu không
        """
        return self.is_monitoring
