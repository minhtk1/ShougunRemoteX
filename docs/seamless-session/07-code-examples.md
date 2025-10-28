# Code Examples - Xpra Seamless Session

Tài liệu này chứa các code examples hoàn chỉnh, sẵn sàng chạy để tham khảo.

## Example 1: Minimal Client (Console Only)

Client tối giản chỉ in ra console, không có GUI:

```python
#!/usr/bin/env python3
"""
Minimal Xpra client - logs all packets to console
No GUI, just for understanding protocol
"""

import socket
import struct
import lz4.block
import pickle  # Using pickle instead of rencodeplus for simplicity

class MinimalXpraClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
    
    def connect(self):
        """Connect to server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"✓ Connected to {self.host}:{self.port}")
    
    def send_packet(self, packet_list):
        """Encode and send packet"""
        # Encode payload
        payload = pickle.dumps(packet_list)
        
        # Compress
        compressed = lz4.block.compress(payload)
        
        # Build header
        header = struct.pack(
            "!BBBBI",
            ord('P'),    # Magic
            16,          # Flags (rencodeplus)
            0x15,        # Compression (lz4 level 5)
            0,           # Chunk index
            len(compressed)
        )
        
        # Send
        self.sock.sendall(header + compressed)
    
    def recv_packet(self):
        """Receive and decode packet"""
        # Read header
        header = self.recv_exact(8)
        magic, flags, comp, chunk, size = struct.unpack("!BBBBI", header)
        
        # Read payload
        payload = self.recv_exact(size)
        
        # Decompress
        if comp > 0:
            payload = lz4.block.decompress(payload)
        
        # Decode
        packet = pickle.loads(payload)
        return packet
    
    def recv_exact(self, size):
        """Receive exactly size bytes"""
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def run(self):
        """Main loop"""
        # Send hello
        print("→ Sending hello...")
        self.send_packet(["hello", {
            "version": "6.3.0",
            "platform": "linux",
            "windows": True,
            "encodings": ["rgb", "png"],
        }])
        
        # Receive and print packets
        while True:
            packet = self.recv_packet()
            packet_type = packet[0]
            
            print(f"← Received: {packet_type}")
            
            if packet_type == "hello":
                caps = packet[1]
                print(f"  Server version: {caps.get('version')}")
                print(f"  Session type: {caps.get('session_type')}")
            
            elif packet_type == "startup-complete":
                print("  Session ready!")
            
            elif packet_type == "new-window":
                wid, x, y, w, h = packet[1:6]
                metadata = packet[6]
                print(f"  Window {wid}: {metadata.get('title')}")
                print(f"  Position: ({x}, {y}), Size: {w}x{h}")
                
                # Acknowledge
                self.send_packet(["map-window", wid, x, y, w, h, {}])
            
            elif packet_type == "draw":
                wid, x, y, w, h = packet[1:6]
                coding = packet[6]
                data_size = len(packet[7])
                seq = packet[8]
                print(f"  Window {wid}: draw {w}x{h} at ({x},{y})")
                print(f"  Encoding: {coding}, Data: {data_size} bytes")
                
                # Acknowledge
                self.send_packet([
                    "damage-sequence", seq, wid, w, h, 10, ""
                ])
            
            elif packet_type == "disconnect":
                reason = packet[1] if len(packet) > 1 else "unknown"
                print(f"  Reason: {reason}")
                break
            
            elif packet_type == "ping":
                import time
                timestamp = packet[1]
                self.send_packet([
                    "ping_echo", timestamp, int(time.time() * 1000), 10000
                ])

# Usage
if __name__ == "__main__":
    client = MinimalXpraClient("localhost", 10000)
    client.connect()
    client.run()
```

**Run:**
```bash
# Terminal 1: Start server
xpra start :100 --bind-tcp=0.0.0.0:10000 --start=xterm

# Terminal 2: Run client
python minimal_client.py
```

## Example 2: Complete GUI Client with Qt6

Full-featured client với Qt6 GUI:

```python
#!/usr/bin/env python3
"""
Complete Xpra Seamless Client with Qt6
Supports: multiple windows, mouse, keyboard, window management
"""

import sys
import socket
import struct
import threading
import time
from io import BytesIO
from typing import Dict

import lz4.block
from PIL import Image

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QMouseEvent, QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal, QObject

# Use actual rencodeplus if available
try:
    from xpra.net.rencodeplus import rencode
except ImportError:
    import pickle as rencode
    print("Warning: Using pickle instead of rencodeplus")


class SignalBridge(QObject):
    """Bridge for cross-thread signals"""
    new_window = pyqtSignal(int, int, int, int, int, dict)
    lost_window = pyqtSignal(int)
    draw_window = pyqtSignal(int, int, int, int, int, str, bytes, int, int)
    update_title = pyqtSignal(int, str)


class XpraWindow(QMainWindow):
    """Individual Xpra window"""
    
    def __init__(self, client, wid, x, y, width, height, metadata):
        super().__init__()
        
        self.client = client
        self.wid = wid
        self.metadata = metadata
        
        # Window properties
        title = metadata.get("title", f"Window {wid}")
        self.setWindowTitle(title)
        self.setGeometry(x, y, width, height)
        
        # Override-redirect (frameless)
        if metadata.get("override-redirect"):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
        
        # Create canvas
        self.canvas = QPixmap(width, height)
        self.canvas.fill(Qt.GlobalColor.white)
        
        # Display widget
        self.label = QLabel()
        self.label.setPixmap(self.canvas)
        self.label.setMouseTracking(True)
        self.setCentralWidget(self.label)
        
        # Event filters
        self.label.mouseMoveEvent = self.mouse_move_event
        self.label.mousePressEvent = self.mouse_press_event
        self.label.mouseReleaseEvent = self.mouse_release_event
        self.label.wheelEvent = self.wheel_event
        
        print(f"Created window {wid}: {title} ({width}x{height})")
    
    def draw(self, x, y, width, height, coding, data, rowstride):
        """Render image data"""
        try:
            start = time.time()
            
            # Decode image
            if coding in ("rgb", "rgb24"):
                img = Image.frombytes("RGB", (width, height), data)
            elif coding == "png":
                img = Image.open(BytesIO(data))
                if img.mode != "RGB":
                    img = img.convert("RGB")
            elif coding == "jpeg":
                img = Image.open(BytesIO(data))
                if img.mode != "RGB":
                    img = img.convert("RGB")
            else:
                print(f"Unsupported encoding: {coding}")
                return -1
            
            # Convert to QImage
            img_data = img.tobytes("raw", "RGB")
            qimg = QImage(
                img_data,
                img.width, img.height,
                img.width * 3,
                QImage.Format.Format_RGB888
            ).copy()
            
            # Draw to canvas
            painter = QPainter(self.canvas)
            painter.drawImage(x, y, qimg)
            painter.end()
            
            # Update display
            self.label.setPixmap(self.canvas)
            
            decode_time = int((time.time() - start) * 1000)
            return decode_time
            
        except Exception as e:
            print(f"Draw error: {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    # Mouse Events
    
    def mouse_move_event(self, event: QMouseEvent):
        pos = event.pos()
        self.client.send_packet([
            "pointer-position",
            self.wid,
            (pos.x(), pos.y()),
            [],  # modifiers
            []   # buttons
        ])
    
    def mouse_press_event(self, event: QMouseEvent):
        button = event.button()
        pos = event.pos()
        
        button_map = {
            Qt.MouseButton.LeftButton: 1,
            Qt.MouseButton.MiddleButton: 2,
            Qt.MouseButton.RightButton: 3,
        }
        button_num = button_map.get(button, 0)
        
        if button_num:
            self.client.send_packet([
                "button-action",
                self.wid,
                button_num,
                True,
                (pos.x(), pos.y()),
                [],
                [button_num]
            ])
    
    def mouse_release_event(self, event: QMouseEvent):
        button = event.button()
        pos = event.pos()
        
        button_map = {
            Qt.MouseButton.LeftButton: 1,
            Qt.MouseButton.MiddleButton: 2,
            Qt.MouseButton.RightButton: 3,
        }
        button_num = button_map.get(button, 0)
        
        if button_num:
            self.client.send_packet([
                "button-action",
                self.wid,
                button_num,
                False,
                (pos.x(), pos.y()),
                [],
                []
            ])
    
    def wheel_event(self, event):
        pos = event.position()
        delta = event.angleDelta()
        
        dx = delta.x() / 120.0
        dy = delta.y() / 120.0
        
        self.client.send_packet([
            "wheel-motion",
            self.wid,
            dx, dy,
            (int(pos.x()), int(pos.y())),
            []
        ])
    
    # Keyboard Events
    
    def keyPressEvent(self, event: QKeyEvent):
        self._send_key_event(event, True)
    
    def keyReleaseEvent(self, event: QKeyEvent):
        self._send_key_event(event, False)
    
    def _send_key_event(self, event: QKeyEvent, pressed: bool):
        keyname = event.text()
        keycode = event.key()
        
        # Get key name from Qt key
        key_str = event.key()
        
        self.client.send_packet([
            "key-action",
            self.wid,
            keyname if keyname else f"key-{keycode}",
            pressed,
            [],  # modifiers
            keycode,
            keyname,
            0, 0
        ])
    
    # Window Events
    
    def closeEvent(self, event):
        print(f"Close window {self.wid}")
        self.client.send_packet(["close-window", self.wid])
        event.accept()
    
    def resizeEvent(self, event):
        size = event.size()
        
        # Resize canvas
        new_canvas = QPixmap(size.width(), size.height())
        new_canvas.fill(Qt.GlobalColor.white)
        
        # Copy old content
        painter = QPainter(new_canvas)
        painter.drawPixmap(0, 0, self.canvas)
        painter.end()
        
        self.canvas = new_canvas
        self.label.setPixmap(self.canvas)
        
        # Notify server
        self.client.send_packet([
            "configure-window",
            self.wid,
            self.x(), self.y(),
            size.width(), size.height(),
            {}
        ])
    
    def moveEvent(self, event):
        pos = event.pos()
        self.client.send_packet([
            "configure-window",
            self.wid,
            pos.x(), pos.y(),
            self.width(), self.height(),
            {}
        ])
    
    def focusInEvent(self, event):
        self.client.send_packet(["focus", self.wid, []])


class XpraClient:
    """Main Xpra client"""
    
    def __init__(self):
        self.sock = None
        self.windows: Dict[int, XpraWindow] = {}
        self.running = False
        self.capabilities = {}
        
        # Signal bridge for thread-safe GUI updates
        self.signals = SignalBridge()
        self.signals.new_window.connect(self._create_window)
        self.signals.lost_window.connect(self._destroy_window)
        self.signals.draw_window.connect(self._draw_window)
        self.signals.update_title.connect(self._update_title)
    
    def connect(self, host, port):
        """Connect to Xpra server"""
        print(f"Connecting to {host}:{port}...")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
        print("✓ Connected!")
        
        # Send hello
        self.send_hello()
        
        # Start receive thread
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()
    
    def send_hello(self):
        """Send client hello"""
        import os
        
        hello = ["hello", {
            "version": "6.3.0",
            "platform": sys.platform,
            "username": os.getenv("USER", "user"),
            "uuid": "python-qt6-client",
            
            "windows": True,
            "keyboard": True,
            "mouse": True,
            
            "encodings": ["png", "jpeg", "rgb"],
            "encoding": "auto",
            
            "desktop_size": (1920, 1080),
            "dpi": 96,
        }]
        
        self.send_packet(hello)
        print("→ Sent hello")
    
    def send_packet(self, packet_list):
        """Encode and send packet"""
        # Encode
        payload = rencode.dumps(packet_list)
        
        # Compress
        compressed = lz4.block.compress(payload)
        
        # Header
        header = struct.pack(
            "!BBBBI",
            ord('P'), 16, 0x15, 0, len(compressed)
        )
        
        # Send
        self.sock.sendall(header + compressed)
    
    def _receive_loop(self):
        """Receive packets"""
        while self.running:
            try:
                packet = self._recv_packet()
                self._handle_packet(packet)
            except Exception as e:
                print(f"Receive error: {e}")
                break
    
    def _recv_packet(self):
        """Receive one packet"""
        # Header
        header = self._recv_exact(8)
        _, _, comp, _, size = struct.unpack("!BBBBI", header)
        
        # Payload
        payload = self._recv_exact(size)
        
        # Decompress
        if comp > 0:
            payload = lz4.block.decompress(payload)
        
        # Decode
        return rencode.loads(payload)
    
    def _recv_exact(self, size):
        """Receive exactly size bytes"""
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def _handle_packet(self, packet):
        """Dispatch packet"""
        if not packet:
            return
        
        ptype = packet[0]
        
        if ptype == "hello":
            self.capabilities = packet[1]
            print(f"← Server hello: {self.capabilities.get('version')}")
        
        elif ptype == "startup-complete":
            print("← Startup complete")
            self.send_packet(["desktop_size", 1920, 1080, 1920, 1080, []])
        
        elif ptype == "new-window":
            wid, x, y, w, h, metadata = packet[1:7]
            self.signals.new_window.emit(wid, x, y, w, h, metadata)
        
        elif ptype == "new-override-redirect":
            wid, x, y, w, h, metadata = packet[1:7]
            metadata["override-redirect"] = True
            self.signals.new_window.emit(wid, x, y, w, h, metadata)
        
        elif ptype == "lost-window":
            wid = packet[1]
            self.signals.lost_window.emit(wid)
        
        elif ptype == "draw":
            wid, x, y, w, h = packet[1:6]
            coding, data, seq = packet[6:9]
            rowstride = packet[9] if len(packet) > 9 else 0
            self.signals.draw_window.emit(wid, x, y, w, h, coding, data, seq, rowstride)
        
        elif ptype == "window-metadata":
            wid, metadata = packet[1:3]
            if "title" in metadata:
                self.signals.update_title.emit(wid, metadata["title"])
        
        elif ptype == "ping":
            timestamp = packet[1]
            self.send_packet([
                "ping_echo", timestamp, int(time.time() * 1000), 10000
            ])
        
        elif ptype == "disconnect":
            reason = packet[1] if len(packet) > 1 else "unknown"
            print(f"← Disconnected: {reason}")
            self.running = False
    
    # GUI operations (called from Qt thread via signals)
    
    def _create_window(self, wid, x, y, w, h, metadata):
        """Create native window"""
        window = XpraWindow(self, wid, x, y, w, h, metadata)
        self.windows[wid] = window
        window.show()
        
        # Send map-window
        self.send_packet(["map-window", wid, x, y, w, h, {}])
    
    def _destroy_window(self, wid):
        """Destroy window"""
        window = self.windows.pop(wid, None)
        if window:
            window.close()
    
    def _draw_window(self, wid, x, y, w, h, coding, data, seq, rowstride):
        """Draw to window"""
        window = self.windows.get(wid)
        if window:
            decode_time = window.draw(x, y, w, h, coding, data, rowstride)
            self.send_packet([
                "damage-sequence", seq, wid, w, h, decode_time, ""
            ])
    
    def _update_title(self, wid, title):
        """Update window title"""
        window = self.windows.get(wid)
        if window:
            window.setWindowTitle(title)
    
    def close(self):
        """Shutdown client"""
        self.running = False
        if self.sock:
            try:
                self.send_packet(["disconnect", "client closing"])
            except:
                pass
            self.sock.close()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    client = XpraClient()
    
    try:
        # Connect to server
        client.connect("localhost", 10000)
        
        # Run Qt event loop
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    main()
```

**Run:**
```bash
# Install dependencies
pip install PyQt6 lz4 Pillow

# Start server
xpra start :100 --bind-tcp=0.0.0.0:10000 --start=xterm --start=firefox

# Run client
python complete_client.py
```

## Example 3: Server Emulator for Testing

Fake server để test client mà không cần Xpra server thật:

```python
#!/usr/bin/env python3
"""
Fake Xpra server for testing clients
Sends dummy window and draw packets
"""

import socket
import struct
import threading
import time
import lz4.block

try:
    from xpra.net.rencodeplus import rencode
except ImportError:
    import pickle as rencode


class FakeXpraServer:
    """Fake server that simulates Xpra protocol"""
    
    def __init__(self, port=10000):
        self.port = port
        self.sock = None
        self.client = None
        self.running = False
    
    def start(self):
        """Start server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))
        self.sock.listen(1)
        
        print(f"Fake Xpra server listening on port {self.port}")
        print("Waiting for client...")
        
        self.client, addr = self.sock.accept()
        print(f"Client connected from {addr}")
        
        self.running = True
        
        # Handle client
        self.handle_client()
    
    def send_packet(self, packet_list):
        """Send packet to client"""
        payload = rencode.dumps(packet_list)
        compressed = lz4.block.compress(payload)
        
        header = struct.pack(
            "!BBBBI",
            ord('P'), 16, 0x15, 0, len(compressed)
        )
        
        self.client.sendall(header + compressed)
        print(f"→ Sent: {packet_list[0]}")
    
    def recv_packet(self):
        """Receive packet from client"""
        # Header
        header = self.recv_exact(8)
        _, _, comp, _, size = struct.unpack("!BBBBI", header)
        
        # Payload
        payload = self.recv_exact(size)
        
        if comp > 0:
            payload = lz4.block.decompress(payload)
        
        packet = rencode.loads(payload)
        print(f"← Received: {packet[0]}")
        return packet
    
    def recv_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self.client.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Client disconnected")
            data += chunk
        return data
    
    def handle_client(self):
        """Handle client connection"""
        # Wait for hello
        hello = self.recv_packet()
        print(f"Client version: {hello[1].get('version')}")
        
        # Send server hello
        self.send_packet(["hello", {
            "version": "6.3.0",
            "platform": "linux",
            "session_type": "seamless",
            "encodings": ["rgb", "png"],
            "windows": True,
        }])
        
        # Send startup-complete
        time.sleep(0.5)
        self.send_packet(["startup-complete"])
        
        # Wait for desktop_size
        self.recv_packet()
        
        # Send fake window
        time.sleep(0.5)
        self.send_fake_window()
        
        # Keep alive with pings
        ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
        ping_thread.start()
        
        # Process client packets
        while self.running:
            try:
                packet = self.recv_packet()
                ptype = packet[0]
                
                if ptype == "map-window":
                    wid = packet[1]
                    self.send_fake_draw(wid)
                
                elif ptype == "damage-sequence":
                    pass  # Acknowledged
                
                elif ptype == "disconnect":
                    print("Client disconnected")
                    break
                
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def send_fake_window(self):
        """Send fake window packet"""
        print("\n→ Sending fake window...")
        
        self.send_packet([
            "new-window",
            1,  # wid
            100, 100,  # x, y
            800, 600,  # width, height
            {
                "title": "Fake Window",
                "class-instance": ("test", "Test"),
            }
        ])
    
    def send_fake_draw(self, wid):
        """Send fake draw packet"""
        print(f"\n→ Sending fake draw for window {wid}...")
        
        # Create fake image: red to blue gradient
        width, height = 800, 600
        pixels = bytearray()
        
        for y in range(height):
            for x in range(width):
                r = int(255 * (1 - x / width))
                g = 0
                b = int(255 * (x / width))
                pixels.extend([r, g, b])
        
        self.send_packet([
            "draw",
            wid,
            0, 0,  # x, y
            width, height,
            "rgb",
            bytes(pixels),
            1,  # sequence
            width * 3  # rowstride
        ])
    
    def ping_loop(self):
        """Send ping every 5 seconds"""
        while self.running:
            time.sleep(5)
            try:
                self.send_packet(["ping", int(time.time() * 1000)])
            except:
                break


if __name__ == "__main__":
    server = FakeXpraServer(port=10000)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
```

**Test:**
```bash
# Terminal 1: Run fake server
python fake_server.py

# Terminal 2: Run your client
python complete_client.py
```

## Example 4: Packet Sniffer/Logger

Tool để capture và phân tích Xpra packets:

```python
#!/usr/bin/env python3
"""
Xpra packet sniffer - logs all traffic between client and server
Acts as transparent proxy
"""

import socket
import struct
import threading
import lz4.block

try:
    from xpra.net.rencodeplus import rencode
except ImportError:
    import pickle as rencode


class XpraPacketSniffer:
    """Intercepts and logs Xpra packets"""
    
    def __init__(self, listen_port, server_host, server_port):
        self.listen_port = listen_port
        self.server_host = server_host
        self.server_port = server_port
    
    def start(self):
        """Start sniffer"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.listen_port))
        sock.listen(1)
        
        print(f"Sniffer listening on port {self.listen_port}")
        print(f"Will forward to {self.server_host}:{self.server_port}\n")
        
        client_sock, addr = sock.accept()
        print(f"Client connected from {addr}\n")
        
        # Connect to real server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((self.server_host, self.server_port))
        print(f"Connected to server\n")
        
        # Forward in both directions
        t1 = threading.Thread(
            target=self.forward,
            args=(client_sock, server_sock, "Client → Server"),
            daemon=True
        )
        t2 = threading.Thread(
            target=self.forward,
            args=(server_sock, client_sock, "Server → Client"),
            daemon=True
        )
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    
    def forward(self, src, dst, label):
        """Forward packets and log them"""
        while True:
            try:
                # Read packet
                packet_data = self.recv_packet(src)
                
                # Parse and log
                try:
                    packet = self.decode_packet(packet_data)
                    self.log_packet(label, packet)
                except Exception as e:
                    print(f"{label}: [decode error: {e}]")
                
                # Forward
                dst.sendall(packet_data)
                
            except Exception as e:
                print(f"{label}: Connection closed")
                break
    
    def recv_packet(self, sock):
        """Receive one packet"""
        # Header
        header = self.recv_exact(sock, 8)
        size = struct.unpack("!I", header[4:8])[0]
        
        # Payload
        payload = self.recv_exact(sock, size)
        
        return header + payload
    
    def recv_exact(self, sock, size):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def decode_packet(self, packet_data):
        """Decode packet"""
        _, _, comp, _, _ = struct.unpack("!BBBBI", packet_data[:8])
        payload = packet_data[8:]
        
        if comp > 0:
            payload = lz4.block.decompress(payload)
        
        return rencode.loads(payload)
    
    def log_packet(self, label, packet):
        """Pretty print packet"""
        ptype = packet[0]
        
        print(f"\n{'='*60}")
        print(f"{label}: {ptype}")
        print(f"{'='*60}")
        
        if ptype == "hello":
            caps = packet[1]
            print(f"  Version: {caps.get('version')}")
            print(f"  Platform: {caps.get('platform')}")
            print(f"  Session type: {caps.get('session_type')}")
            print(f"  Encodings: {caps.get('encodings')}")
        
        elif ptype in ("new-window", "new-override-redirect"):
            wid, x, y, w, h = packet[1:6]
            metadata = packet[6]
            print(f"  WID: {wid}")
            print(f"  Position: ({x}, {y})")
            print(f"  Size: {w}x{h}")
            print(f"  Title: {metadata.get('title')}")
            print(f"  Class: {metadata.get('class-instance')}")
        
        elif ptype == "draw":
            wid, x, y, w, h = packet[1:6]
            coding = packet[6]
            data_len = len(packet[7])
            seq = packet[8]
            print(f"  WID: {wid}")
            print(f"  Region: ({x}, {y}) {w}x{h}")
            print(f"  Encoding: {coding}")
            print(f"  Data size: {data_len} bytes")
            print(f"  Sequence: {seq}")
        
        elif ptype == "damage-sequence":
            seq, wid, w, h, decode_time = packet[1:6]
            print(f"  Sequence: {seq}")
            print(f"  WID: {wid}")
            print(f"  Size: {w}x{h}")
            print(f"  Decode time: {decode_time}ms")
        
        else:
            print(f"  Data: {packet[1:]}")


if __name__ == "__main__":
    # Usage: Client connects to 10001, sniffer forwards to real server at 10000
    sniffer = XpraPacketSniffer(
        listen_port=10001,
        server_host="localhost",
        server_port=10000
    )
    sniffer.start()
```

**Usage:**
```bash
# Start real server
xpra start :100 --bind-tcp=0.0.0.0:10000 --start=xterm

# Start sniffer (in another terminal)
python packet_sniffer.py

# Connect client to sniffer port
xpra attach tcp://localhost:10001/
```

---

## Kết luận

Các examples trên cung cấp:

1. **Minimal Client**: Hiểu cơ bản protocol flow
2. **Complete Client**: Full implementation với Qt6
3. **Fake Server**: Test client mà không cần Xpra thật
4. **Packet Sniffer**: Debug và phân tích traffic

Bạn có thể sử dụng các examples này làm foundation để build client của riêng mình!

---

**Previous:** [Hướng dẫn Implementation](06-implementation.md) | **Back to:** [README](README.md)

