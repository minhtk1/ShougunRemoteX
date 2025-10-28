# Quy trình Kết nối Seamless Session

## Tổng quan Connection Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│         CONNECTION LIFECYCLE                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Transport Connection                                 │
│     ↓                                                    │
│  2. Protocol Negotiation                                 │
│     ↓                                                    │
│  3. Hello Exchange                                       │
│     ↓                                                    │
│  4. Authentication (if required)                         │
│     ↓                                                    │
│  5. Capability Negotiation                               │
│     ↓                                                    │
│  6. Session Establishment                                │
│     ↓                                                    │
│  7. Active Session (window forwarding)                   │
│     ↓                                                    │
│  8. Disconnection                                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 1. Transport Connection

### Các loại Transport được hỗ trợ

#### TCP Socket
```python
# Server listen
xpra start :100 --bind-tcp=0.0.0.0:10000

# Client connect
xpra attach tcp://server.example.com:10000/
```

#### Unix Domain Socket (Local)
```python
# Server tự động tạo socket
xpra start :100
# Creates: /run/user/1000/xpra/HOST-100

# Client connect
xpra attach :100
```

#### SSH Tunnel
```python
# Single command (recommended)
xpra start ssh://user@server/ --start=xterm

# Behind the scenes:
# 1. SSH connection to server
# 2. Start xpra server on remote
# 3. Tunnel socket over SSH
# 4. Local client attaches via tunnel
```

#### WebSocket
```python
# Server enable websocket
xpra start :100 --bind-ws=0.0.0.0:10000

# HTML5 client connect
http://server.example.com:10000/index.html
```

#### SSL/TLS
```python
# Server with SSL
xpra start :100 \
  --bind-ssl=0.0.0.0:10000 \
  --ssl-cert=/path/to/cert.pem \
  --ssl-key=/path/to/key.pem

# Client connect
xpra attach ssl://server.example.com:10000/
```

#### QUIC (Modern)
```python
# Lower latency, better for poor networks
xpra start :100 --bind-quic=0.0.0.0:10000
xpra attach quic://server.example.com:10000/
```

### Connection Initialization

```python
# Client side pseudo-code
class XpraClient:
    def connect(self, connection_string):
        # 1. Parse connection string
        transport, host, port, display = parse_url(connection_string)
        
        # 2. Establish transport connection
        if transport == "tcp":
            sock = socket.connect(host, port)
        elif transport == "ssh":
            sock = setup_ssh_tunnel(host, port)
        elif transport == "ssl":
            sock = ssl_wrap_socket(socket.connect(host, port))
        
        # 3. Create protocol handler
        self.protocol = Protocol(sock)
        self.protocol.start()
        
        # 4. Start packet processing
        self.start_packet_handlers()
        
        return self.protocol
```

## 2. Protocol Negotiation

### Initial Handshake

```
CLIENT                                  SERVER
  │                                       │
  ├──[TCP SYN]──────────────────────────►│
  │◄─[TCP SYN-ACK]────────────────────── │
  ├──[TCP ACK]──────────────────────────►│
  │                                       │
  │  Connection established               │
  │                                       │
```

### Protocol Version Detection

Server có thể phát hiện và hỗ trợ nhiều protocols:

```python
# Server checks first bytes
def identify_protocol(data):
    if data.startswith(b'P'):
        return 'xpra'
    elif data.startswith(b'RFB'):
        return 'rfb'  # VNC
    elif data.startswith(b'GET '):
        return 'http'
    elif data.startswith(b'SSH'):
        return 'ssh'
    else:
        return 'unknown'
```

## 3. Hello Exchange

### Client Hello

Client gửi packet đầu tiên:

```python
["hello", {
    # Version info
    "version": "6.3.0",
    "client_type": "Python/Qt6",
    
    # Platform info
    "platform": "win32",
    "platform.name": "Windows",
    "platform.release": "11",
    "platform.platform": "Windows-11-10.0.26200",
    
    # Machine info
    "hostname": "DESKTOP-ABC123",
    "username": "user",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    
    # Capabilities
    "windows": True,
    "keyboard": True,
    "mouse": True,
    "clipboard": True,
    "notifications": True,
    "audio": True,
    
    # Encoding support
    "encodings": ["h264", "vp9", "png", "jpeg", "rgb"],
    "encodings.core": ["rgb24", "rgb32"],
    "encodings.with_quality": ["jpeg", "webp"],
    "encodings.with_speed": ["h264", "vp9", "av1"],
    "encoding": "auto",  # Preferred encoding
    
    # Video decoding capabilities
    "encoding.h264.decoder": "nvdec",  # NVIDIA GPU decode
    "encoding.vp9.decoder": "software",
    
    # Display info
    "desktops": 1,
    "desktop_size": (1920, 1080),
    "screen_sizes": [
        (0, 0, 1920, 1080, 527, 296, 0, 0, "HDMI-1")
    ],
    "dpi": 96,
    
    # Compression support
    "compressors": ["lz4", "brotli"],
    "compression_level": 5,
    
    # Encryption (if needed)
    "cipher": "AES-GCM",
    "cipher.key_size": 256,
    
    # Performance hints
    "batch.delay": 10,  # ms
    "batch.max_events": 100,
    
    # Feature flags
    "windows.raise": True,
    "windows.frame_sizes": True,
    "windows.decorations": True,
    "file-transfer": True,
    "printing": True,
    "open-files": True,
}]
```

### Server Hello

Server phản hồi với capabilities của nó:

```python
["hello", {
    # Version
    "version": "6.3.0",
    "server_type": "Python/gtk-x11",
    
    # Platform
    "platform": "linux",
    "platform.name": "Linux",
    "platform.release": "6.5.0",
    
    # Display info
    "display": ":100",
    "display_name": ":100",
    "actual_desktop_size": (1920, 1080),
    
    # Session info
    "session_type": "seamless",  # ⭐ IMPORTANT!
    "windows": True,
    "server-window-resize": True,
    
    # Encoding capabilities
    "encodings": ["h264", "vp9", "png", "jpeg", "rgb"],
    "encodings.core": ["rgb24", "rgb32"],
    "encoding.h264.encoder": "nvenc",  # NVIDIA GPU encode
    "encoding.vp9.encoder": "libvpx",
    
    # Compression
    "compressors": ["lz4", "brotli"],
    
    # Audio
    "audio": True,
    "sound.send": True,
    "sound.receive": True,
    "sound.encoders": ["opus", "vorbis"],
    
    # Clipboard
    "clipboard.enabled": True,
    "clipboard.selections": ["CLIPBOARD", "PRIMARY"],
    
    # Packet aliases (optimization)
    "aliases": {
        1: "new-window",
        2: "lost-window",
        3: "draw",
        4: "window-metadata",
        5: "raise-window",
        6: "button-action",
        7: "key-action",
        8: "damage-sequence",
        # ...
    },
    
    # Features
    "notifications": True,
    "bell": True,
    "cursors": True,
    "named_cursors": True,
    "file-transfer": True,
    "printing": True,
    
    # Window management
    "window.raise": True,
    "window.resize-counter": True,
    "window.configure.pointer": True,
    "window-icon-encodings": ["png", "premult_argb32"],
}]
```

## 4. Authentication

Nếu server yêu cầu authentication:

### Challenge-Response Flow

```
CLIENT                                  SERVER
  │                                       │
  ├──["hello", {...}]───────────────────►│
  │                                       │
  │                         [Check auth required]
  │                                       │
  │◄──["challenge", challenge, digest]───┤
  │                                       │
  ├─[Compute response]                    │
  │                                       │
  ├──["challenge-response", response]───►│
  │                                       │
  │                          [Verify response]
  │                                       │
  │◄──["hello", {...}]────────────────────┤
  │                                       │
  │  [Connection authenticated]           │
  │                                       │
```

### Authentication Methods

#### 1. Password (env)
```python
# Server
xpra start :100 --auth=env

# Reads password from XPRA_PASSWORD environment variable
```

#### 2. Password (file)
```python
# Server
xpra start :100 --auth=file:filename=/etc/xpra/passwords.txt

# Client
xpra attach tcp://server/ --password-file=~/.xpra/password
```

#### 3. HMAC
```python
# Challenge-Response with HMAC-SHA256
challenge = os.urandom(32)
server_sends(["challenge", challenge, "hmac+sha256"])

# Client computes
response = hmac.new(password.encode(), challenge, sha256).digest()
client_sends(["challenge-response", response])

# Server verifies
expected = hmac.new(stored_password.encode(), challenge, sha256).digest()
if response == expected:
    authenticated = True
```

#### 4. SSH (implicit)
```bash
# SSH connection provides authentication
# No additional auth needed
xpra start ssh://user@server/
```

#### 5. Multi-factor
```python
# Server
xpra start :100 --auth=file,sys

# Requires both file password AND system password
```

### Authentication Example Code

```python
class XpraClient:
    def handle_challenge(self, packet):
        challenge_data = packet[1]
        digest_type = packet[2]  # "hmac+sha256"
        
        # Get password from user or config
        password = self.get_password()
        
        # Compute response based on digest type
        if digest_type == "hmac+sha256":
            import hmac
            from hashlib import sha256
            response = hmac.new(
                password.encode('utf-8'),
                challenge_data,
                sha256
            ).digest()
        
        # Send response
        self.send("challenge-response", response)
    
    def handle_authentication_failed(self, packet):
        reason = packet[1]
        print(f"Authentication failed: {reason}")
        self.disconnect()
```

## 5. Capability Negotiation

Sau hello exchange, client và server negotiate common capabilities:

```python
class XpraClient:
    def parse_server_capabilities(self, server_caps):
        # Determine common encodings
        client_encodings = set(self.caps["encodings"])
        server_encodings = set(server_caps["encodings"])
        self.encodings = client_encodings & server_encodings
        
        # Choose best encoding
        if "h264" in self.encodings and self.has_hw_decoder:
            self.preferred_encoding = "h264"
        elif "vp9" in self.encodings:
            self.preferred_encoding = "vp9"
        else:
            self.preferred_encoding = "png"
        
        # Set compression
        if "lz4" in server_caps["compressors"]:
            self.compressor = "lz4"
        else:
            self.compressor = None
        
        # Check session type
        if server_caps.get("session_type") != "seamless":
            raise Exception("Server is not in seamless mode!")
        
        # Store server capabilities
        self.server_caps = server_caps
```

## 6. Session Establishment

### Startup Complete

Server gửi startup-complete khi sẵn sàng:

```python
["startup-complete"]
```

Client responds với các settings:

```python
# Client → Server: Set desktop size
["desktop_size", 1920, 1080, 1920, 1080, [
    (0, 0, 1920, 1080, 527, 296, 0, 0, "HDMI-1")
]]

# Client → Server: Set encoding preferences
["encoding", "auto"]
["quality", 90]
["speed", 50]

# Client → Server: Enable features
["set-clipboard-enabled", True]
["set-keyboard-sync-enabled", True]
```

### Load Existing Windows

Nếu attach vào session đang chạy, server gửi tất cả existing windows:

```python
# Server → Client: Send all windows
for wid in existing_windows:
    send_new_window_packet(wid)
    send_initial_draw_packet(wid)
```

## 7. Active Session

Sau khi establish, session vào steady state:

```
┌─────────────────────────────────────────────────────┐
│              ACTIVE SESSION STATE                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Server ──[new-window]────────────────────► Client │
│  Server ──[draw packets]──────────────────► Client │
│  Server ──[window-metadata]───────────────► Client │
│  Server ◄─[damage-sequence]───────────────  Client │
│  Server ◄─[input events]──────────────────  Client │
│  Server ◄─[configure-window]──────────────  Client │
│  Server ◄─[focus]─────────────────────────  Client │
│  Server ◄─[close-window]──────────────────  Client │
│                                                     │
│  Server ←→[ping/ping_echo]────────────────→ Client │
│  Server ←→[clipboard]─────────────────────→ Client │
│  Server ──[sound-data]────────────────────► Client │
│  Server ◄─[sound-data]────────────────────  Client │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Keep-Alive

```python
# Server periodically sends ping
every 5_seconds:
    server.send("ping", current_timestamp())

# Client responds
def handle_ping(packet):
    server_time = packet[1]
    self.send("ping_echo", server_time, 
              current_timestamp(), 
              timeout_value)
```

## 8. Disconnection

### Graceful Disconnect

```python
# Client closes cleanly
client.send("disconnect", "user closed client")
client.close()

# Server closes cleanly
server.send("disconnect", "server shutting down")
server.close()
```

### Network Failure

```python
# Client detects connection loss
if no_packets_received_for(timeout):
    client.handle_connection_lost()
    client.attempt_reconnect()  # if configured

# Server detects client disconnect
if no_ping_echo_for(timeout):
    server.cleanup_client(protocol)
```

### Reconnection

```python
# Client reconnects với same UUID
client.caps["uuid"] = saved_uuid

# Server recognizes returning client
if uuid in previous_clients:
    # Restore session state
    # Send existing windows again
    restore_client_session(uuid)
```

## Complete Connection Example

```python
#!/usr/bin/env python3
import socket
import struct
from typing import Any

class SimpleXpraClient:
    def __init__(self):
        self.sock = None
        self.capabilities = {}
    
    def connect(self, host: str, port: int):
        """Establish TCP connection"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        print(f"Connected to {host}:{port}")
    
    def send_packet(self, packet_data: list):
        """Send Xpra packet"""
        # 1. Encode with rencodeplus
        from xpra.net.rencodeplus import rencode
        payload = rencode.dumps(packet_data)
        
        # 2. Optional: compress with lz4
        import lz4.block
        compressed = lz4.block.compress(payload)
        compression = 0x15  # lz4 level 5
        
        # 3. Build header
        header = struct.pack(
            "!BBBBBBBB",
            ord('P'),        # Magic byte
            16,              # Protocol flags (rencodeplus)
            compression,     # Compression
            0,               # Chunk index (main packet)
            0, 0, 0, 0       # Payload size (filled below)
        )
        
        # 4. Set payload size
        size = len(compressed)
        header = header[:4] + struct.pack("!I", size)
        
        # 5. Send
        self.sock.sendall(header + compressed)
    
    def recv_packet(self) -> list:
        """Receive Xpra packet"""
        # 1. Read header
        header = self.sock.recv(8)
        if len(header) < 8:
            raise Exception("Connection closed")
        
        magic, flags, comp, chunk = header[:4]
        size = struct.unpack("!I", header[4:8])[0]
        
        # 2. Read payload
        payload = b""
        while len(payload) < size:
            chunk = self.sock.recv(size - len(payload))
            payload += chunk
        
        # 3. Decompress if needed
        if comp > 0:
            import lz4.block
            payload = lz4.block.decompress(payload)
        
        # 4. Decode rencodeplus
        from xpra.net.rencodeplus import rencode
        packet = rencode.loads(payload)
        
        return packet
    
    def handshake(self):
        """Perform hello exchange"""
        # Send client hello
        hello_caps = {
            "version": "6.3.0",
            "platform": "linux",
            "windows": True,
            "encodings": ["png", "jpeg", "rgb"],
        }
        self.send_packet(["hello", hello_caps])
        print("Sent hello")
        
        # Receive server hello or challenge
        packet = self.recv_packet()
        packet_type = packet[0]
        
        if packet_type == "challenge":
            # Handle authentication
            self.handle_challenge(packet)
            packet = self.recv_packet()
            packet_type = packet[0]
        
        if packet_type == "hello":
            self.capabilities = packet[1]
            print(f"Received server hello: {self.capabilities.get('version')}")
        else:
            raise Exception(f"Unexpected packet: {packet_type}")
    
    def main_loop(self):
        """Process packets"""
        while True:
            packet = self.recv_packet()
            packet_type = packet[0]
            
            if packet_type == "new-window":
                self.handle_new_window(packet)
            elif packet_type == "draw":
                self.handle_draw(packet)
            elif packet_type == "disconnect":
                print(f"Server disconnect: {packet[1]}")
                break
            # ... handle other packet types

# Usage
client = SimpleXpraClient()
client.connect("localhost", 10000)
client.handshake()
client.main_loop()
```

---

**Next:** [Quản lý Windows](04-window-management.md)

