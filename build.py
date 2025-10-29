"""
Script đơn giản để build Python service thành .exe
"""

import subprocess
import sys
import psutil
import time
from pathlib import Path


def kill_existing_processes():
    """Kill tất cả các process ShougunRemoteX_Service đang chạy trước khi build."""
    process_name = "ShougunRemoteX_Service"
    killed_processes = []
    
    print("Checking for running ShougunRemoteX_Service processes...")
    
    # Tìm và kill tất cả processes có tên giống nhau
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Kiểm tra tên process chính xác
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
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
    
    if killed_processes:
        print(f"Killed {len(killed_processes)} existing processes")
        # Đợi một chút để các process được kill hoàn toàn
        time.sleep(3)
    else:
        print("No existing processes found")
    
    return killed_processes


def build_exe():
    """Build Python service thành executable."""
    
    print("Building ShougunRemoteX Service to .exe...")
    
    # Kill các process cũ trước khi build
    kill_existing_processes()
    
    # Xóa file exe cũ nếu tồn tại để tránh PermissionError
    exe_path = Path("dist/ShougunRemoteX_Service.exe")
    if exe_path.exists():
        try:
            exe_path.unlink()
            print("Removed existing exe file")
        except PermissionError:
            print("Warning: Could not remove existing exe file, but continuing...")
    
    # PyInstaller command với hidden imports và paths
    cmd = [
        "pyinstaller",
        "--onefile",  # Tạo 1 file .exe duy nhất
        "--windowed",  # Không hiển thị console window
        "--name", "ShougunRemoteX_Service",
        "--add-data", "src;src",  # Include src folder
        "--add-data", "config;config",  # Include config folder
        # Hidden imports để đảm bảo PyInstaller tìm thấy tất cả modules
        "--hidden-import", "psutil",
        "--hidden-import", "pywin32",
        "--hidden-import", "pythonnet",
        "--hidden-import", "pydantic",
        "--hidden-import", "loguru",
        "--hidden-import", "yaml",
        "--hidden-import", "shougun_remote",
        "--hidden-import", "shougun_remote.services",
        "--hidden-import", "shougun_remote.core",
        "--hidden-import", "shougun_remote.config",
        "--hidden-import", "shougun_remote.models",
        "--hidden-import", "shougun_remote.repositories",
        "--hidden-import", "shougun_remote.monitors",
        "--hidden-import", "watchdog",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        # Thêm paths để PyInstaller tìm thấy modules
        "--paths", "src",
        "--paths", ".",
        "python_service.py"  # Main script
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("Build successful!")
        print("Executable: dist/ShougunRemoteX_Service.exe")
        
        # Kiểm tra xem file exe đã được tạo thành công chưa
        if exe_path.exists():
            print(f"✓ Executable created successfully: {exe_path.absolute()}")
        else:
            print("⚠ Warning: Executable file not found after build")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = build_exe()
    
    if success:
        print("\nBuild completed!")
        print("Your .exe file is ready in 'dist' folder")
    else:
        print("\nBuild failed!")
        sys.exit(1)
