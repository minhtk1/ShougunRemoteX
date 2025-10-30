from __future__ import annotations

import traceback

from shougun_remote.core.interfaces import IRemoteClient
from xpra.scripts.main import (
    make_client,
    do_run_client,
    connect_to_server,
    bypass_no_gtk,
    configure_network,
    InitException,
    InitInfo,
    InitExit,
)
from xpra.scripts.config import make_defaults_struct, fixup_options
from xpra.log import Logger

log = Logger("shougun", "client")
from xpra.scripts.parsing import parse_display_name


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
        opts.clipboard = "yes" if options.get("clipboard", True) else "no"
        opts.notifications = options.get("notifications", False)
        opts.modal_windows = options.get("modal_windows", True)
        opts.reconnect = options.get("reconnect", True)
        opts.keyboard_raw = options.get("keyboard_raw", False)
        opts.webcam = str(options.get("webcam", "no")).lower()
        opts.printing = str(options.get("printing", "no")).lower()
        opts.file_transfer = str(options.get("file_transfer", "no")).lower()
        audio_value = str(options.get("audio", "no")).lower()
        audio_enabled = audio_value in {"yes", "true", "1", "on"}
        opts.audio = audio_value
        opts.speaker = "on" if audio_enabled else "disabled"
        opts.microphone = "on" if audio_enabled else "disabled"
        opts.packet_encoders = ["yaml"]
        opts.compressors = ["none"]
        opts.compression_level = 0

        # Ensure gtk backend
        opts.backend = "gtk"
        # mirror xpra CLI initialisation so capability negotiation is correct
        fixup_options(opts)
        log.info("client encodings (post-fixup): %s", opts.encodings)
        log.info("client default encoding: %s", opts.encoding)
        print(f"[XpraRemoteClient] encodings={opts.encodings}")
        print(f"[XpraRemoteClient] default-encoding={opts.encoding}")
        configure_network(opts)
        log.info("enabled packet encoders: %s", opts.packet_encoders)
        log.info("enabled compressors: %s", opts.compressors)
        print(f"[XpraRemoteClient] packet-encoders={opts.packet_encoders}")
        print(f"[XpraRemoteClient] compressors={opts.compressors}")

        # Create client app and connect
        # PyInstaller runtime hooks may pre-load Gtk, bypass the strict check.
        bypass_no_gtk(True)
        raw_url = options.pop("raw_url", None)
        display_path = options.pop("display_path", "")

        if raw_url:
            url = raw_url
        else:
            if port <= 0:
                raise ValueError("Port must be specified when no raw URL is provided")
            suffix = ""
            if display_path:
                suffix = f"/{display_path.strip('/')}"
            url = f"tcp://{host}:{int(port)}{suffix or '/'}"

        app = make_client(opts)
        try:
            app.init(opts)
            # gtk client relies on UI init to register mixins (encodings, etc.)
            app.init_ui(opts)
        except (InitExit, InitException, InitInfo):
            raise
        except Exception:
            tb = traceback.format_exc()
            log.error("client init failed:\n%s", tb)
            print(f"[XpraRemoteClient] init failed:\n{tb}")
            raise
        if not hasattr(app, "printing"):
            app.printing = False
        display_desc = parse_display_name(ValueError, opts, url, cmdline=[url])
        display_desc["retry"] = bool(opts.reconnect)
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
