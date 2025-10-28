# ShougunRemoteX Python Service

Dự án Python chuẩn SOLID có thể chạy như standalone service hoặc build thành .exe.

## Quick Start

### 1. Setup
```bash
pip install -r requirements.txt
```

### 2. Test Python Service
```bash
python examples/basic_usage.py
```

### 3. Run Standalone Service
```bash
python python_service.py
```

### 4. Build to .exe
```bash
python build.py
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python CLI    │───▶│  Python Service │───▶│   Background    │
│                 │    │                 │    │     Tasks       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Executable    │    │ SOLID Design    │    │ Data Storage    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## SOLID Principles Implementation

- **S**ingle Responsibility: Mỗi class có một trách nhiệm duy nhất
- **O**pen/Closed: Mở để mở rộng, đóng để sửa đổi  
- **L**iskov Substitution: Derived classes thay thế được base classes
- **I**nterface Segregation: Interfaces nhỏ và tập trung
- **D**ependency Inversion: Phụ thuộc vào abstractions

## Features

✅ **Python Service**: Background service với threading  
✅ **Standalone Executable**: Build thành .exe độc lập  
✅ **Configuration**: JSON/YAML config management  
✅ **Logging**: Structured logging với loguru  
✅ **Data Persistence**: File-based repository  
✅ **Unit Tests**: Comprehensive test coverage  
✅ **Dependency Injection**: Container và factory pattern  

## File Structure

```
├── src/shougun_remote/          # Python source code
│   ├── core/                    # Interfaces & abstractions
│   ├── services/                # Service implementations  
│   ├── models/                  # Data models
│   ├── config/                  # Configuration management
│   └── repositories/            # Data access layer
├── config/                      # Configuration files
├── examples/                    # Usage examples
├── tests/                       # Unit tests
├── python_service.py           # Main service entry point
├── build.py                    # Build script for .exe
└── requirements.txt            # Dependencies
```

## API Usage

### Python
```python
from shougun_remote.services.factory import ServiceFactory

service = ServiceFactory.create_shougun_service()
service.start()
print(service.get_status())
service.stop()
```

### Executable
```bash
# Chạy service
python python_service.py

# Hoặc chạy .exe sau khi build
dist/ShougunRemoteX_Service.exe
```

## Configuration

Edit `config/service.json`:
```json
{
  "service": {
    "name": "ShougunRemoteX",
    "version": "1.0.0"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/shougun_service.log"
  },
  "performance": {
    "worker_thread_sleep": 1.0,
    "max_memory_mb": 512
  }
}
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Format code
black src/ tests/ examples/
flake8 src/ tests/ examples/

# Type checking
mypy src/
```

## Troubleshooting

### Python Service Issues
- Kiểm tra Python version >= 3.11.9
- Kiểm tra dependencies: `pip install -r requirements.txt`
- Kiểm tra config file: `config/service.json`

### Build Issues
- Kiểm tra PyInstaller đã cài đặt: `pip install pyinstaller`
- Kiểm tra Python version >= 3.11.9
- Kiểm tra file `python_service.py` tồn tại

## License

MIT License - Xem LICENSE file để biết thêm chi tiết.

## Support

Tạo issue trên GitHub repository nếu gặp vấn đề.