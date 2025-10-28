"""
Script đơn giản để build Python service thành .exe
"""

import subprocess
import sys
from pathlib import Path


def build_exe():
    """Build Python service thành executable."""
    
    print("Building ShougunRemoteX Service to .exe...")
    
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
        result = subprocess.run(cmd, check=True)
        
        print("Build successful!")
        print("Executable: dist/ShougunRemoteX_Service.exe")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
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
