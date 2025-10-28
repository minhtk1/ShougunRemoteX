"""
Configuration models và implementations.
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path
import json
import yaml
from ..core.config_interface import IConfigManager


class ConfigManager(IConfigManager):
    """
    Implementation của IConfigManager.
    
    Tuân thủ Single Responsibility Principle (SRP):
    - Chỉ quản lý cấu hình
    
    Tuân thủ Open/Closed Principle (OCP):
    - Mở để mở rộng các format khác nhau
    """
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = None
    
    def load_config(self, config_path: Union[str, Path]) -> bool:
        """Tải cấu hình từ file."""
        try:
            self._config_path = Path(config_path)
            
            if not self._config_path.exists():
                return False
            
            with open(self._config_path, 'r', encoding='utf-8') as f:
                if self._config_path.suffix.lower() == '.json':
                    self._config = json.load(f)
                elif self._config_path.suffix.lower() in ['.yml', '.yaml']:
                    self._config = yaml.safe_load(f)
                else:
                    return False
            
            return True
        except Exception:
            return False
    
    def save_config(self, config_path: Union[str, Path]) -> bool:
        """Lưu cấu hình ra file."""
        try:
            config_path = Path(config_path)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                else:
                    return False
            
            return True
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị cấu hình theo key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Đặt giá trị cấu hình."""
        try:
            keys = key.split('.')
            config = self._config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            return True
        except Exception:
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Lấy toàn bộ section cấu hình."""
        return self.get(section, {})
    
    def has_key(self, key: str) -> bool:
        """Kiểm tra key có tồn tại không."""
        return self.get(key) is not None
    
    def get_all(self) -> Dict[str, Any]:
        """Lấy toàn bộ cấu hình."""
        return self._config.copy()
