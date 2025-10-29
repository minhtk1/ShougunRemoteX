"""
Setup script để cài đặt và cấu hình dự án.
"""

import os
import sys
import subprocess
from pathlib import Path


def create_directories():
    """Tạo các thư mục cần thiết."""
    directories = [
        "logs",
        "data", 
        "config",
        "tests",
        "examples"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")


def install_dependencies():
    """Cài đặt dependencies."""
    try:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    return True


def create_sample_config():
    """Tạo file cấu hình mẫu."""
    config_content = """{
  "service": {
    "name": "ShougunRemoteX",
    "version": "1.0.0",
    "description": "Python SOLID Service for C# Integration"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/shougun_service.log",
    "rotation": "1 day",
    "retention": "30 days"
  },
  "data": {
    "tasks_file": "data/tasks.json",
    "backup_enabled": true,
    "backup_interval": "1 hour"
  },
  "performance": {
    "worker_thread_sleep": 1.0,
    "max_memory_mb": 512,
    "cpu_threshold": 80.0
  },
  "integration": {
    "csharp_bridge_enabled": true,
    "api_port": 8080,
    "timeout_seconds": 30
  }
}"""
    
    config_path = Path("config/service.json")
    if not config_path.exists():
        config_path.write_text(config_content, encoding="utf-8")
        print("Created sample configuration file")
    else:
        print("Configuration file already exists")


def run_tests():
    """Chạy tests."""
    try:
        print("Running tests...")
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("All tests passed")
    except subprocess.CalledProcessError as e:
        print(f"Some tests failed: {e}")
        return False
    return True


def main():
    """Main setup function."""
    print("Setting up ShougunRemoteX Python Service...")
    print("Required Python version: >= 3.11.9")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11.9 or higher is required. Current version: {sys.version}")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed: Could not install dependencies")
        sys.exit(1)
    
    # Create sample config
    create_sample_config()
    
    # Run tests
    if not run_tests():
        print("Setup completed with test failures")
    else:
        print("Setup completed successfully!")
    
    print("\nNext steps:")
    print("1. Run 'python examples/basic_usage.py' to test the service")
    print("2. Check 'config/service.json' for configuration options")


if __name__ == "__main__":
    main()
