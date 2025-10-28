# Hướng dẫn Implementation Xpra Seamless Client

Tài liệu này hướng dẫn chi tiết cách build một Xpra client từ đầu để connect và hiển thị seamless windows.

## Kiến trúc Client Tối thiểu

```python
┌─────────────────────────────────────────────────────┐
│              MINIMAL XPRA CLIENT                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. NetworkConnection                               │
│     - Socket management                             │
│     - Packet framing                                │
│                                                     │
│  2. ProtocolHandler                                 │
│     - rencodeplus encode/decode                     │
│     - Compression/decompression                     │
│                                                     │
│  3. PacketDispatcher                                │
│     - Route packets to handlers                     │
│                                                     │
│  4. WindowManager                                   │
│     - Track windows (wid → window)                  │
│     - Create/destroy native windows                 │
│                                                     │
│  5. Renderer                                        │
│     - Decode pixel data                             │
│     - Draw to windows                               │
│                                                     │
│  6. InputHandler                                    │
│     - Capture mouse/keyboard                        │
│     - Send to server                                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Bước 1: Setup Dependencies

### Python Dependencies

```bash
pip install PyQt6           # GUI framework
pip install lz4             # Compression
pip install Pillow          # Image decoding
pip install av              # Video decoding (optional)
```

### File Structure

```
xpra_client/
├── __init__.py
├── network.py          # Network connection
├── protocol.py         # Protocol handler
├── client.py           # Main client class
├── window.py           # Window implementation
├── renderer.py         # Rendering logic
└── main.py            # Entry point
```

## Bước 2: Network Layer

### network.py

```python
import socket
import struct
from typing import Callable

class NetworkConnection:
    """Manages TCP socket connection"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.packet_handler: Callable = None
    
    def connect(self):
        """Establish connection"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        print(f"Connected to {self.host}:{self.port}")
    
    def send_packet(self, packet_data: bytes):
        """Send raw packet data"""
        self.sock.sendall(packet_data)
    
    def recv_exact(self, size: int) -> bytes:
        """Receive exactly size bytes"""
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data
    
    def recv_packet(self) -> bytes:
        """Receive one complete packet"""
        # Read 8-byte header
        header = self.recv_exact(8)
        
        # Parse header
        magic = header[0]
        if magic != ord('P'):
            raise ValueError(f"Invalid magic byte: {magic}")
        
        flags = header[1]
        compression = header[2]
        chunk_index = header[3]
        payload_size = struct.unpack("!I", header[4:8])[0]
        
        # Read payload
        payload = self.recv_exact(payload_size)
        
        return header + payload
    
    def close(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            self.sock = None
```

## Bước 3: Protocol Layer

### protocol.py

```python
import struct
import lz4.block

# For rencodeplus, we'll use a simplified implementation
# In production, use xpra.net.rencodeplus.rencode
try:
    from xpra.net.rencodeplus import rencode
except ImportError:
    # Fallback: use pickle (NOT RECOMMENDED for production)
    import pickle as rencode

class ProtocolHandler:
    """Handles packet encoding/decoding"""
    
    def encode_packet(self, packet_list: list) -> bytes:
        """Encode packet to bytes"""
        # 1. Encode payload with rencodeplus
        payload = rencode.dumps(packet_list)
        
        # 2. Compress with lz4
        compressed = lz4.block.compress(payload)
        compression_byte = 0x15  # lz4 level 5
        
        # 3. Build header
        magic = ord('P')
        flags = 16  # rencodeplus
        chunk_index = 0  # main packet
        payload_size = len(compressed)
        
        header = struct.pack(
            "!BBBBL",
            magic,
            flags,
            compression_byte,
            chunk_index,
            payload_size
        )
        
        return header + compressed
    
    def decode_packet(self, packet_data: bytes) -> list:
        """Decode packet from bytes"""
        # Parse header
        magic, flags, compression, chunk, size = struct.unpack(
            "!BBBBL", packet_data[:8]
        )
        
        # Extract payload
        payload = packet_data[8:]
        
        # Decompress if needed
        if compression > 0:
            payload = lz4.block.decompress(payload)
        
        # Decode with rencodeplus
        packet = rencode.loads(payload)
        
        return packet
```

## Bước 4: Main Client Class

### client.py

```python
import threading
from typing import Dict
from .network import NetworkConnection
from .protocol import ProtocolHandler
from .window import ClientWindow

class XpraClient:
    """Main Xpra client implementation"""
    
    def __init__(self):
        self.network = None
        self.protocol = ProtocolHandler()
        self.windows: Dict[int, ClientWindow] = {}
        self.running = False
        self.capabilities = {}
        
        # Packet handlers
        self.packet_handlers = {
            "hello": self._handle_hello,
            "startup-complete": self._handle_startup_complete,
            "new-window": self._handle_new_window,
            "new-override-redirect": self._handle_new_or_window,
            "lost-window": self._handle_lost_window,
            "raise-window": self._handle_raise_window,
            "draw": self._handle_draw,
            "window-metadata": self._handle_window_metadata,
            "disconnect": self._handle_disconnect,
            "ping": self._handle_ping,
        }
    
    def connect(self, host: str, port: int):
        """Connect to Xpra server"""
        print(f"Connecting to {host}:{port}...")
        
        # Establish connection
        self.network = NetworkConnection(host, port)
        self.network.connect()
        
        # Send hello
        self.send_hello()
        
        # Start receive loop
        self.running = True
        self.receive_thread = threading.Thread(
            target=self._receive_loop,
            daemon=True
        )
        self.receive_thread.start()
    
    def send_hello(self):
        """Send client hello packet"""
        hello = ["hello", {
            "version": "6.3.0",
            "platform": "linux",
            "username": "user",
            "uuid": "python-client-001",
            
            # Capabilities
            "windows": True,
            "keyboard": True,
            "mouse": True,
            
            # Encodings
            "encodings": ["png", "jpeg", "rgb"],
            "encoding": "auto",
            
            # Display
            "desktop_size": (1920, 1080),
            "dpi": 96,
        }]
        
        self.send_packet(hello)
        print("Sent hello packet")
    
    def send_packet(self, packet: list):
        """Send packet to server"""
        data = self.protocol.encode_packet(packet)
        self.network.send_packet(data)
    
    def _receive_loop(self):
        """Receive and process packets"""
        while self.running:
            try:
                # Receive packet
                packet_data = self.network.recv_packet()
                
                # Decode packet
                packet = self.protocol.decode_packet(packet_data)
                
                # Dispatch
                self._dispatch_packet(packet)
                
            except Exception as e:
                print(f"Error in receive loop: {e}")
                self.running = False
                break
    
    def _dispatch_packet(self, packet: list):
        """Route packet to appropriate handler"""
        if not packet:
            return
        
        packet_type = packet[0]
        
        # Get handler
        handler = self.packet_handlers.get(packet_type)
        
        if handler:
            handler(packet)
        else:
            print(f"Unhandled packet type: {packet_type}")
    
    # Packet Handlers
    
    def _handle_hello(self, packet: list):
        """Handle server hello"""
        self.capabilities = packet[1]
        print(f"Server version: {self.capabilities.get('version')}")
        print(f"Session type: {self.capabilities.get('session_type')}")
        
        # Verify seamless mode
        if self.capabilities.get("session_type") != "seamless":
            print("WARNING: Server is not in seamless mode!")
    
    def _handle_startup_complete(self, packet: list):
        """Handle startup complete"""
        print("Session established!")
        
        # Send desktop size
        self.send_packet(["desktop_size", 1920, 1080, 1920, 1080, [
            (0, 0, 1920, 1080, 527, 296, 0, 0, "screen0")
        ]])
    
    def _handle_new_window(self, packet: list):
        """Handle new window"""
        wid = packet[1]
        x, y = packet[2], packet[3]
        width, height = packet[4], packet[5]
        metadata = packet[6]
        
        print(f"New window {wid}: {metadata.get('title', 'Untitled')}")
        
        # Create native window
        window = ClientWindow(self, wid, x, y, width, height, metadata)
        self.windows[wid] = window
        
        # Show window
        window.show()
        
        # Send map-window
        self.send_packet(["map-window", wid, x, y, width, height, {}])
    
    def _handle_new_or_window(self, packet: list):
        """Handle override-redirect window"""
        # Same as new-window but mark as OR
        packet[6]["override-redirect"] = True
        self._handle_new_window(packet)
    
    def _handle_lost_window(self, packet: list):
        """Handle window closed"""
        wid = packet[1]
        
        window = self.windows.pop(wid, None)
        if window:
            print(f"Lost window {wid}")
            window.close()
    
    def _handle_raise_window(self, packet: list):
        """Handle raise window"""
        wid = packet[1]
        
        window = self.windows.get(wid)
        if window:
            window.raise_()
    
    def _handle_draw(self, packet: list):
        """Handle draw packet"""
        wid = packet[1]
        x, y = packet[2], packet[3]
        width, height = packet[4], packet[5]
        coding = packet[6]
        data = packet[7]
        sequence = packet[8]
        rowstride = packet[9] if len(packet) > 9 else 0
        
        window = self.windows.get(wid)
        if window:
            # Render
            decode_time = window.draw(x, y, width, height, 
                                     coding, data, rowstride)
            
            # Send acknowledgment
            self.send_packet([
                "damage-sequence",
                sequence, wid, width, height,
                decode_time, ""
            ])
    
    def _handle_window_metadata(self, packet: list):
        """Handle metadata update"""
        wid = packet[1]
        metadata = packet[2]
        
        window = self.windows.get(wid)
        if window:
            window.update_metadata(metadata)
    
    def _handle_disconnect(self, packet: list):
        """Handle disconnect"""
        reason = packet[1] if len(packet) > 1 else "Unknown"
        print(f"Server disconnected: {reason}")
        self.running = False
    
    def _handle_ping(self, packet: list):
        """Handle ping"""
        timestamp = packet[1]
        
        # Send pong
        import time
        self.send_packet([
            "ping_echo",
            timestamp,
            int(time.time() * 1000),
            10000  # timeout
        ])
    
    def close(self):
        """Close client"""
        self.running = False
        
        # Close all windows
        for window in list(self.windows.values()):
            window.close()
        
        # Disconnect
        if self.network:
            self.send_packet(["disconnect", "client closing"])
            self.network.close()
```

## Bước 5: Window Implementation

### window.py

```python
from PyQt6.QtWidgets import QMainWindow, QLabel
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt
from PIL import Image
import io
import time

class ClientWindow(QMainWindow):
    """Native window for displaying remote content"""
    
    def __init__(self, client, wid, x, y, width, height, metadata):
        super().__init__()
        
        self.client = client
        self.wid = wid
        self.metadata = metadata
        
        # Setup window
        self.setWindowTitle(metadata.get("title", f"Window {wid}"))
        self.move(x, y)
        self.resize(width, height)
        
        # Override-redirect windows
        if metadata.get("override-redirect"):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
        
        # Create canvas
        self.canvas = QPixmap(width, height)
        self.canvas.fill(Qt.GlobalColor.white)
        
        # Label to display canvas
        self.label = QLabel()
        self.label.setPixmap(self.canvas)
        self.setCentralWidget(self.label)
        
        # Mouse tracking
        self.label.setMouseTracking(True)
        self.label.mouseMoveEvent = self.on_mouse_move
        self.label.mousePressEvent = self.on_mouse_press
        self.label.mouseReleaseEvent = self.on_mouse_release
        
        # Keyboard events
        self.keyPressEvent = self.on_key_press
        self.keyReleaseEvent = self.on_key_release
        
        # Window events
        self.closeEvent = self.on_close
        self.resizeEvent = self.on_resize
        self.moveEvent = self.on_move
        self.focusInEvent = self.on_focus_in
    
    def draw(self, x, y, width, height, coding, data, rowstride):
        """Render image data to window"""
        start = time.time()
        
        try:
            # Decode based on encoding
            if coding == "rgb" or coding == "rgb24":
                img = self._decode_rgb(data, width, height, rowstride)
            elif coding == "png":
                img = self._decode_png(data)
            elif coding == "jpeg":
                img = self._decode_jpeg(data)
            else:
                print(f"Unsupported encoding: {coding}")
                return 0
            
            # Convert to QPixmap
            qimg = self._pil_to_qimage(img)
            
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
            return -1
    
    def _decode_rgb(self, data, width, height, rowstride):
        """Decode RGB data"""
        img = Image.frombytes("RGB", (width, height), data)
        return img
    
    def _decode_png(self, data):
        """Decode PNG data"""
        img = Image.open(io.BytesIO(data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    
    def _decode_jpeg(self, data):
        """Decode JPEG data"""
        img = Image.open(io.BytesIO(data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img
    
    def _pil_to_qimage(self, pil_img):
        """Convert PIL Image to QImage"""
        data = pil_img.tobytes("raw", "RGB")
        qimg = QImage(
            data,
            pil_img.width,
            pil_img.height,
            pil_img.width * 3,
            QImage.Format.Format_RGB888
        )
        return qimg.copy()  # Copy to avoid data being freed
    
    def update_metadata(self, metadata):
        """Update window metadata"""
        if "title" in metadata:
            self.setWindowTitle(metadata["title"])
    
    # Event Handlers
    
    def on_mouse_move(self, event):
        """Mouse moved"""
        pos = event.pos()
        self.client.send_packet([
            "pointer-position",
            self.wid,
            (pos.x(), pos.y()),
            [],  # modifiers
            []   # buttons
        ])
    
    def on_mouse_press(self, event):
        """Mouse button pressed"""
        button = event.button()
        pos = event.pos()
        
        button_num = {
            Qt.MouseButton.LeftButton: 1,
            Qt.MouseButton.MiddleButton: 2,
            Qt.MouseButton.RightButton: 3,
        }.get(button, 0)
        
        if button_num:
            self.client.send_packet([
                "button-action",
                self.wid,
                button_num,
                True,  # pressed
                (pos.x(), pos.y()),
                [],  # modifiers
                [button_num]
            ])
    
    def on_mouse_release(self, event):
        """Mouse button released"""
        button = event.button()
        pos = event.pos()
        
        button_num = {
            Qt.MouseButton.LeftButton: 1,
            Qt.MouseButton.MiddleButton: 2,
            Qt.MouseButton.RightButton: 3,
        }.get(button, 0)
        
        if button_num:
            self.client.send_packet([
                "button-action",
                self.wid,
                button_num,
                False,  # released
                (pos.x(), pos.y()),
                [],
                []
            ])
    
    def on_key_press(self, event):
        """Key pressed"""
        keyname = event.text()
        keycode = event.key()
        
        self.client.send_packet([
            "key-action",
            self.wid,
            keyname,
            True,  # pressed
            [],    # modifiers
            keycode,
            keyname,
            0, 0
        ])
    
    def on_key_release(self, event):
        """Key released"""
        keyname = event.text()
        keycode = event.key()
        
        self.client.send_packet([
            "key-action",
            self.wid,
            keyname,
            False,  # released
            [],
            keycode,
            keyname,
            0, 0
        ])
    
    def on_close(self, event):
        """Window close requested"""
        self.client.send_packet(["close-window", self.wid])
        event.accept()
    
    def on_resize(self, event):
        """Window resized"""
        size = event.size()
        
        # Resize canvas
        self.canvas = self.canvas.scaled(
            size.width(),
            size.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio
        )
        
        # Notify server
        self.client.send_packet([
            "configure-window",
            self.wid,
            self.x(), self.y(),
            size.width(), size.height(),
            {}
        ])
    
    def on_move(self, event):
        """Window moved"""
        pos = event.pos()
        
        self.client.send_packet([
            "configure-window",
            self.wid,
            pos.x(), pos.y(),
            self.width(), self.height(),
            {}
        ])
    
    def on_focus_in(self, event):
        """Window focused"""
        self.client.send_packet(["focus", self.wid, []])
```

## Bước 6: Entry Point

### main.py

```python
import sys
from PyQt6.QtWidgets import QApplication
from client import XpraClient

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create client
    client = XpraClient()
    
    # Connect to server
    host = "localhost"
    port = 10000
    
    try:
        client.connect(host, port)
        
        # Run Qt event loop
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.close()

if __name__ == "__main__":
    main()
```

## Usage

```bash
# 1. Start Xpra server
xpra start :100 --bind-tcp=0.0.0.0:10000 --start=xterm

# 2. Run client
python main.py
```

## Extending the Client

### Add Video Decoding

```python
# Install: pip install av

import av

class VideoDecoder:
    def __init__(self):
        self.decoders = {}
    
    def get_decoder(self, coding):
        if coding not in self.decoders:
            self.decoders[coding] = av.CodecContext.create(coding, "r")
        return self.decoders[coding]
    
    def decode_video_frame(self, coding, data):
        decoder = self.get_decoder(coding)
        packet = av.Packet(data)
        frames = decoder.decode(packet)
        
        if frames:
            frame = frames[0]
            img = frame.to_image()
            return img
        
        return None
```

### Add Authentication

```python
import hmac
from hashlib import sha256

def _handle_challenge(self, packet):
    challenge = packet[1]
    digest_type = packet[2]
    
    password = input("Password: ")
    
    if digest_type == "hmac+sha256":
        response = hmac.new(
            password.encode(),
            challenge,
            sha256
        ).digest()
    
    self.send_packet(["challenge-response", response])
```

### Add Clipboard Support

```python
from PyQt6.QtWidgets import QApplication

def setup_clipboard(self):
    clipboard = QApplication.clipboard()
    clipboard.dataChanged.connect(self.on_clipboard_change)

def on_clipboard_change(self):
    text = QApplication.clipboard().text()
    
    self.send_packet([
        "clipboard-token",
        "CLIPBOARD",
        "text/plain",
        text.encode()
    ])
```

---

**Next:** [Code Examples](07-code-examples.md)

