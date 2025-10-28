"""
Python service entry point - standalone service.
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shougun_remote.services.factory import ServiceFactory


def main():
    """Main entry point cho Python service."""
    try:
        print("Starting ShougunRemoteX Python Service...")
        
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
