from __future__ import annotations

from shougun_remote.core.interfaces import IRemoteClient
from xpra.scripts.main import (
    make_client,
    do_run_client,
    connect_to_server,
)
from xpra.scripts.config import make_defaults_struct


class XpraRemoteClient(IRemoteClient):
    def __init__(self) -> None:
        self._client = None
        self._opts = None

    def connect(self, host: str, port: int, **options) -> None:
        # Build minimal options structure for our use-case
        opts = make_defaults_struct()
        # Feature flags
        opts.windows = options.get("windows", True)
        opts.dpi = options.get("dpi", 96)
        opts.opengl = options.get("opengl", "no")
        opts.encoding = options.get("encoding", "rgb")
        opts.clipboard = options.get("clipboard", True)
        opts.notifications = options.get("notifications", False)
        opts.modal_windows = options.get("modal_windows", True)
        opts.reconnect = options.get("reconnect", True)
        opts.keyboard_raw = options.get("keyboard_raw", False)

        # Ensure gtk backend
        opts.backend = "gtk"

        # Create client app and connect
        app = make_client(opts)
        display_desc = {
            "type": "tcp",
            "host": host,
            "port": int(port),
            "display": "",  # no display path
            "display_name": f"tcp://{host}:{int(port)}/",
            "retry": bool(opts.reconnect),
        }
        connect_to_server(app, display_desc, opts)

        self._client = app
        self._opts = opts

    def run(self) -> int:
        if not self._client:
            raise RuntimeError("Client not connected. Call connect() first.")
        return int(do_run_client(self._client))

    def quit(self, exit_code: int = 0) -> None:
        if self._client:
            self._client.quit(exit_code)
