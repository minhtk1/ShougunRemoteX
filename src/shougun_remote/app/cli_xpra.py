import sys
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

