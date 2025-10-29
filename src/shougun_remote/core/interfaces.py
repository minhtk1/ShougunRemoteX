from abc import ABC, abstractmethod


class IRemoteClient(ABC):
    @abstractmethod
    def connect(self, host: str, port: int, **options) -> None:
        """Kết nối tới remote server"""

    @abstractmethod
    def run(self) -> int:
        """Chạy client, return exit code"""

    @abstractmethod
    def quit(self, exit_code: int = 0) -> None:
        """Dừng client"""

