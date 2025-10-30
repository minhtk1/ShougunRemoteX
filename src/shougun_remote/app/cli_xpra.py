import sys
import os
import atexit
from datetime import datetime
from urllib.parse import urlparse

IS_FROZEN = getattr(sys, "frozen", False)


def setup_frozen_logging(base_path: str) -> None:
    if not IS_FROZEN:
        return
    exec_dir = os.path.dirname(os.path.abspath(sys.executable))
    logs_dir = os.path.join(exec_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "Xpra_cmd.log")
    log_stream = open(log_file, "a", encoding="utf-8", buffering=1)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_stream.write(f"\n[{timestamp}] Xpra_cmd launch args: {' '.join(sys.argv[1:])}\n")
    sys.stdout = log_stream
    sys.stderr = log_stream

    def _close_stream() -> None:
        try:
            log_stream.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Xpra_cmd exiting\n")
        finally:
            log_stream.close()

    atexit.register(_close_stream)
    os.environ.setdefault("XPRA_LOG_DIR", logs_dir)


if IS_FROZEN:
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

setup_frozen_logging(base_path)

# Setup GTK3 runtime paths TRƯỚC khi import bất kỳ module nào khác
# Điều này quan trọng cho PyInstaller để tìm thấy DLL và typelib files
if IS_FROZEN:
    # PyInstaller tạo biến _MEIPASS chứa đường dẫn đến temp directory
    lib_path = os.path.join(base_path, "lib")
    if os.path.exists(lib_path):
        path = os.environ.get("PATH", "")
        if lib_path not in path:
            os.environ["PATH"] = f"{lib_path}{os.path.pathsep}{path}"
    
    # Thiết lập GI_TYPELIB_PATH cho gi.repository
    girepo_path = os.path.join(base_path, "lib", "girepository-1.0")
    if os.path.exists(girepo_path):
        os.environ["GI_TYPELIB_PATH"] = girepo_path
    
    # Thiết lập GDK_PIXBUF cho gdk-pixbuf loaders
    gdk_pixbuf_dir = os.path.join(lib_path, "gdk-pixbuf-2.0")
    if os.path.exists(gdk_pixbuf_dir):
        for item in os.listdir(gdk_pixbuf_dir):
            loaders_path = os.path.join(gdk_pixbuf_dir, item, "loaders")
            if os.path.isdir(loaders_path):
                cache_file = os.path.join(loaders_path, "loaders.cache")
                if os.path.exists(cache_file):
                    os.environ["GDK_PIXBUF_MODULEDIR"] = loaders_path
                    os.environ["GDK_PIXBUF_MODULE_FILE"] = cache_file
                    break
    
    # GIO_MODULE_DIR cho gio modules
    gio_modules_dir = os.path.join(lib_path, "gio", "modules")
    if os.path.exists(gio_modules_dir):
        os.environ["GIO_MODULE_DIR"] = gio_modules_dir
    
    # FONTCONFIG_FILE cho fontconfig
    etc_path = os.path.join(base_path, "etc")
    if os.path.exists(etc_path):
        fontconfig_conf = os.path.join(etc_path, "fonts", "fonts.conf")
        if os.path.exists(fontconfig_conf):
            os.environ["FONTCONFIG_FILE"] = fontconfig_conf

xpra_share = (
    os.path.join(base_path, "xpra", "share", "xpra")
    if IS_FROZEN
    else os.path.abspath(os.path.join(base_path, "..", "..", "xpra", "share", "xpra"))
)

if os.path.exists(xpra_share):
    # Thiết lập các biến môi trường để xpra tìm đúng thư mục resources khi chạy ở chế độ đóng gói
    os.environ.setdefault("XPRA_APP_DIR", xpra_share)
    os.environ.setdefault("XPRA_RESOURCES_DIR", xpra_share)
    os.environ.setdefault("XPRA_ICON_DIR", os.path.join(xpra_share, "icons"))
    os.environ.setdefault("XPRA_IMAGE_DIR", os.path.join(xpra_share, "images"))

# Import pyinstaller_gtk_runtime để setup GTK3 runtime paths
from shougun_remote.app import pyinstaller_gtk_runtime  # noqa: F401

# Import các module xpra để đảm bảo PyInstaller detect được các module redirect
# Điều này cần thiết để module redirect hoạt động đúng trong PyInstaller build
import xpra  # noqa: F401
import xpra.client  # noqa: F401
import xpra.client.gtk3  # noqa: F401
import xpra.client.gtk3.client  # noqa: F401

import argparse
from shougun_remote.adapters.xpra.client import XpraRemoteClient


def _str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Xpra Remote Desktop Client")
    parser.add_argument("command", help="Command: attach")
    parser.add_argument("url", help="Connection URL: tcp://host:port[/display]")
    parser.add_argument("--windows", default="yes")
    parser.add_argument("--dpi", type=int, default=96)
    parser.add_argument("--opengl", default="no")
    parser.add_argument("--encoding", default="rgb")
    parser.add_argument("--clipboard", default="yes")
    parser.add_argument("--notifications", default="no")
    parser.add_argument("--modal-windows", dest="modal_windows", default="yes")
    parser.add_argument("--reconnect", default="yes")
    parser.add_argument("--keyboard-raw", dest="keyboard_raw", default="no")
    parser.add_argument(
        "--printing",
        choices=["yes", "no", "ask", "auto"],
        default="no",
        help="Printing support (yes|no|ask|auto). Default: no.",
    )
    parser.add_argument(
        "--audio",
        choices=["yes", "no"],
        default="no",
        help="Bật hoặc tắt toàn bộ âm thanh (yes|no). Mặc định: no.",
    )
    args = parser.parse_args()

    if args.command.lower() != "attach":
        print("Only 'attach' is supported", file=sys.stderr)
        return 2
    url = args.url
    parsed = urlparse(url)
    if parsed.scheme != "tcp":
        print("Only tcp:// URLs are supported", file=sys.stderr)
        return 2
    host = parsed.hostname
    port = parsed.port or 0
    display_path = parsed.path.lstrip("/")
    if not host or port < 0:
        print(f"Invalid URL format: {url}", file=sys.stderr)
        return 2

    client = XpraRemoteClient()
    try:
        client.connect(
            host,
            port,
            windows=_str_to_bool(args.windows),
            dpi=args.dpi,
            opengl=args.opengl,
            encoding=args.encoding,
            clipboard=_str_to_bool(args.clipboard),
            notifications=_str_to_bool(args.notifications),
            modal_windows=_str_to_bool(args.modal_windows),
            reconnect=_str_to_bool(args.reconnect),
            keyboard_raw=_str_to_bool(args.keyboard_raw),
            printing=args.printing,
            audio=args.audio,
            raw_url=url,
            display_path=display_path,
        )
        return client.run()
    except Exception as exc:
        print(f"Failed to start Xpra client: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
