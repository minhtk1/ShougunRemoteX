"""
Python service entry point - standalone service.
"""

import sys
import os
import time
import psutil
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shougun_remote.services.factory import ServiceFactory


def kill_existing_processes():
    """Kill tất cả các process ShougunRemoteX_Service đang chạy."""
    current_process = psutil.Process()
    process_name = "ShougunRemoteX_Service"
    killed_processes = []
    
    # Tìm và kill tất cả processes có tên giống nhau
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Kiểm tra tên process chính xác
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                # Bỏ qua process hiện tại
                if proc.info['pid'] != current_process.pid:
                    # Kiểm tra thêm cmdline để đảm bảo đúng process
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('ShougunRemoteX_Service' in arg for arg in cmdline):
                        try:
                            proc.kill()
                            killed_processes.append(proc.info['pid'])
                            print(f"Killed existing process PID: {proc.info['pid']}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return killed_processes


def check_existing_process():
    """Kiểm tra xem đã có process nào đang chạy chưa."""
    current_process = psutil.Process()
    process_name = "ShougunRemoteX_Service"
    
    # Tìm tất cả processes có tên giống nhau
    existing_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Kiểm tra tên process chính xác
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                # Bỏ qua process hiện tại
                if proc.info['pid'] != current_process.pid:
                    # Kiểm tra thêm cmdline để đảm bảo đúng process
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('ShougunRemoteX_Service' in arg for arg in cmdline):
                        existing_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return existing_processes


def main():
    """Main entry point cho Python service."""
    try:
        # Kiểm tra và kill các process cũ đang chạy
        existing_processes = check_existing_process()
        if existing_processes:
            print(f"Found existing ShougunRemoteX Service processes: {existing_processes}")
            print("Killing existing processes to ensure single instance...")
            killed_processes = kill_existing_processes()
            if killed_processes:
                print(f"Killed {len(killed_processes)} existing processes")
                # Đợi một chút để các process được kill hoàn toàn
                time.sleep(2)
            else:
                print("Could not kill existing processes, exiting...")
                sys.exit(1)
        
        print("Starting ShougunRemoteX Python Service...")
        print(f"Process ID: {os.getpid()}")
        
        # Tạo service từ factory
        service = ServiceFactory.create_shougun_service()
        
        # Khởi động service
        if service.start():
            print("Python service started successfully")
            
            # Giữ service chạy
            while True:
                time.sleep(1)
                
        else:
            print("Failed to start Python service")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("Service interrupted by user")
        if 'service' in locals():
            service.stop()
        sys.exit(0)
    except Exception as e:
        print(f"Error in Python service: {e}")
        if 'service' in locals():
            service.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
