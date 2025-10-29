import sys
import os

# Setup GTK3 runtime paths TRƯỚC khi import bất kỳ module nào khác
# Điều này quan trọng cho PyInstaller để tìm thấy DLL và typelib files
if getattr(sys, 'frozen', False):
    # PyInstaller tạo biến _MEIPASS chứa đường dẫn đến temp directory
    base_path = sys._MEIPASS
    
    # Thiết lập PATH để tìm DLL trong thư mục lib
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

# Import các module xpra để đảm bảo PyInstaller detect được các module redirect
# Điều này cần thiết để module redirect hoạt động đúng trong PyInstaller build
import xpra  # noqa: F401
import xpra.client  # noqa: F401
import xpra.client.gtk3  # noqa: F401
import xpra.client.gtk3.client  # noqa: F401

import argparse
from shougun_remote.adapters.xpra.client import XpraRemoteClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Xpra Remote Desktop Client")
    parser.add_argument("command", help="Command: attach")
    parser.add_argument("url", help="Connection URL: tcp://host:port")
    parser.add_argument("--windows", default="yes")
    parser.add_argument("--dpi", type=int, default=96)
    parser.add_argument("--opengl", default="no")
    parser.add_argument("--encoding", default="rgb")
    parser.add_argument("--clipboard", default="yes")
    parser.add_argument("--notifications", default="no")
    parser.add_argument("--modal-windows", dest="modal_windows", default="yes")
    parser.add_argument("--reconnect", default="yes")
    parser.add_argument("--keyboard-raw", dest="keyboard_raw", default="no")
    args = parser.parse_args()

    if args.command.lower() != "attach":
        print("Only 'attach' is supported", file=sys.stderr)
        return 2

    # Parse tcp://host:port
    url = args.url
    if not url.startswith("tcp://"):
        print("Only tcp:// URLs are supported", file=sys.stderr)
        return 2
    try:
        host_port = url.replace("tcp://", "", 1)
        host, port_str = host_port.split(":", 1)
        port = int(port_str)
    except Exception:
        print(f"Invalid URL format: {url}", file=sys.stderr)
        return 2

    client = XpraRemoteClient()
    client.connect(
        host,
        port,
        windows=(args.windows == "yes"),
        dpi=args.dpi,
        opengl=args.opengl,
        encoding=args.encoding,
        clipboard=(args.clipboard == "yes"),
        notifications=(args.notifications == "yes"),
        modal_windows=(args.modal_windows == "yes"),
        reconnect=(args.reconnect == "yes"),
        keyboard_raw=(args.keyboard_raw == "yes"),
    )
    return client.run()


if __name__ == "__main__":
    sys.exit(main())

