"""
JSON Reader - Đọc và xử lý file JSON

Class này đọc file JSON từ folder ShougunIsConnected và xử lý dữ liệu.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger


class JsonReader:
    """Class đọc và xử lý file JSON."""
    
    def __init__(self):
        """Khởi tạo JSON reader."""
        self.processed_files = set()  # Set để theo dõi file đã xử lý
        
    def read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Đọc file JSON và trả về dữ liệu.
        
        Args:
            file_path: Đường dẫn đến file JSON
            
        Returns:
            Dict[str, Any]: Dữ liệu JSON hoặc None nếu có lỗi
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File không tồn tại: {file_path}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Đã đọc file JSON: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi parse JSON từ file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Lỗi đọc file {file_path}: {e}")
            return None
    
    def validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """
        Kiểm tra cấu trúc JSON có hợp lệ không.
        
        Args:
            data: Dữ liệu JSON cần kiểm tra
            
        Returns:
            bool: True nếu hợp lệ, False nếu không
        """
        try:
            # Kiểm tra các trường bắt buộc (có thể tùy chỉnh theo yêu cầu)
            required_fields = ['timestamp', 'status']  # Ví dụ
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Thiếu trường bắt buộc: {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi kiểm tra cấu trúc JSON: {e}")
            return False
    
    def process_json_data(self, file_path: str, data: Dict[str, Any]) -> bool:
        """
        Xử lý dữ liệu JSON.
        
        Args:
            file_path: Đường dẫn file JSON
            data: Dữ liệu JSON
            
        Returns:
            bool: True nếu xử lý thành công, False nếu thất bại
        """
        try:
            # Kiểm tra cấu trúc JSON
            if not self.validate_json_structure(data):
                logger.warning(f"Cấu trúc JSON không hợp lệ: {file_path}")
                return False
            
            # Xử lý dữ liệu (có thể tùy chỉnh theo yêu cầu)
            timestamp = data.get('timestamp')
            status = data.get('status')
            
            logger.info(f"Xử lý dữ liệu JSON từ {file_path}:")
            logger.info(f"  - Timestamp: {timestamp}")
            logger.info(f"  - Status: {status}")
            
            # Thêm vào danh sách đã xử lý
            self.processed_files.add(file_path)
            
            # Có thể thêm logic xử lý khác ở đây
            self._handle_status_change(status, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Lỗi xử lý dữ liệu JSON từ {file_path}: {e}")
            return False
    
    def _handle_status_change(self, status: str, data: Dict[str, Any]):
        """
        Xử lý khi có thay đổi trạng thái.
        
        Args:
            status: Trạng thái mới
            data: Dữ liệu JSON đầy đủ
        """
        try:
            if status == "connected":
                logger.info("Shougun đã kết nối")
                # Xử lý khi kết nối
                self._on_connected(data)
            elif status == "disconnected":
                logger.info("Shougun đã ngắt kết nối")
                # Xử lý khi ngắt kết nối
                self._on_disconnected(data)
            else:
                logger.info(f"Trạng thái không xác định: {status}")
                
        except Exception as e:
            logger.error(f"Lỗi xử lý thay đổi trạng thái: {e}")
    
    def _on_connected(self, data: Dict[str, Any]):
        """
        Xử lý khi Shougun kết nối.
        
        Args:
            data: Dữ liệu JSON
        """
        try:
            logger.info("Xử lý sự kiện kết nối Shougun")
            # Có thể thêm logic xử lý khi kết nối ở đây
            # Ví dụ: gửi thông báo, cập nhật database, etc.
            
        except Exception as e:
            logger.error(f"Lỗi xử lý sự kiện kết nối: {e}")
    
    def _on_disconnected(self, data: Dict[str, Any]):
        """
        Xử lý khi Shougun ngắt kết nối.
        
        Args:
            data: Dữ liệu JSON
        """
        try:
            logger.info("Xử lý sự kiện ngắt kết nối Shougun")
            # Có thể thêm logic xử lý khi ngắt kết nối ở đây
            # Ví dụ: gửi thông báo, cập nhật database, etc.
            
        except Exception as e:
            logger.error(f"Lỗi xử lý sự kiện ngắt kết nối: {e}")
    
    def get_processed_files(self) -> List[str]:
        """
        Lấy danh sách file đã xử lý.
        
        Returns:
            List[str]: Danh sách đường dẫn file đã xử lý
        """
        return list(self.processed_files)
    
    def clear_processed_files(self):
        """Xóa danh sách file đã xử lý."""
        self.processed_files.clear()
        logger.info("Đã xóa danh sách file đã xử lý")
