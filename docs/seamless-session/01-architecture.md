# Kiến trúc Seamless Session

## Tổng quan kiến trúc

Seamless Session được xây dựng trên kiến trúc **Client-Server** với communication protocol tùy chỉnh, được tối ưu cho việc forward individual windows với latency thấp.

## Các thành phần chính

### 1. Server Side Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    XPRA SERVER PROCESS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              X11 Integration Layer                   │  │
│  │  - X11 event monitoring (XComposite, XDamage)       │  │
│  │  - Window detection & tracking                       │  │
│  │  - Input event injection                             │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │          Window Management Layer                     │  │
│  │  - WindowServer mixin                                │  │
│  │  - _id_to_window: {wid: window_model}              │  │
│  │  - _window_to_id: {window_model: wid}              │  │
│  │  - Window lifecycle management                       │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │           Encoding & Compression Layer               │  │
│  │  - Video encoders: h264, vp8, vp9, av1              │  │
│  │  - Image encoders: rgb, png, jpeg, webp             │  │
│  │  - Damage region tracking                            │  │
│  │  - Auto-quality adjustment                           │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │            Protocol Layer                            │  │
│  │  - Packet serialization (rencodeplus)               │  │
│  │  - Compression (lz4, brotli)                        │  │
│  │  - Encryption (AES, SSL)                            │  │
│  │  - Chunking for large data                          │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │          Network Transport Layer                     │  │
│  │  - TCP sockets                                       │  │
│  │  - Unix domain sockets                               │  │
│  │  - WebSocket handler                                 │  │
│  │  - SSL/TLS wrapper                                   │  │
│  │  - SSH integration                                   │  │
│  │  - QUIC support                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Server Components Chi tiết

**1. ServerCore** (`xpra/server/core.py`)
- Base class cho tất cả server types
- Quản lý authentication
- Handle initial handshake
- Connection lifecycle

**2. ServerBase** (`xpra/server/base.py`)
- Extend ServerCore
- Session sharing logic
- Client connection management
- Hello packet processing

**3. WindowServer Mixin** (`xpra/server/mixins/window.py`)
```python
class WindowServer:
    _id_to_window: dict[int, WindowModel]
    _window_to_id: dict[WindowModel, int]
    
    def _add_new_window_common(wid, window):
        # Register window với unique ID
        
    def _do_send_new_window_packet(ptype, window, geometry):
        # Broadcast window tới tất cả clients
        
    def _process_damage_sequence(proto, packet):
        # Xác nhận client đã render xong
```

**4. X11 Server** (specific for seamless)
- Sử dụng **Xvfb** hoặc **Xdummy** làm virtual framebuffer
- XComposite extension: Capture window pixels
- XDamage extension: Track thay đổi
- XTest extension: Inject input events

### 2. Client Side Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    XPRA CLIENT PROCESS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Network Transport Layer                      │  │
│  │  - Connection establishment                          │  │
│  │  - Protocol negotiation                              │  │
│  │  - Keep-alive / ping                                 │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │            Protocol Layer                            │  │
│  │  - Packet deserialization (rencodeplus)             │  │
│  │  - Decompression (lz4, brotli)                      │  │
│  │  - Decryption (AES, SSL)                            │  │
│  │  - Chunk reassembly                                  │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │         Packet Dispatcher                            │  │
│  │  - Route packets theo type                           │  │
│  │  - _process_new_window()                            │  │
│  │  - _process_draw()                                  │  │
│  │  - _process_lost_window()                           │  │
│  │  - _process_window_metadata()                       │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │      Window Management Layer                         │  │
│  │  - windows: {wid: ClientWindow}                     │  │
│  │  - Create/destroy native windows                     │  │
│  │  - Window position/size tracking                     │  │
│  │  - Focus management                                  │  │
│  │  - Modal windows handling                            │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │      Decoding & Rendering Layer                      │  │
│  │  - Video decoders: h264, vp8, vp9, av1              │  │
│  │  - Image decoders: rgb, png, jpeg, webp             │  │
│  │  - Pixel format conversion                           │  │
│  │  - OpenGL rendering (optional)                       │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │       Native Window Integration                      │  │
│  │  - GTK+ widgets (Linux primary)                     │  │
│  │  - Qt widgets (cross-platform)                      │  │
│  │  - Win32 API (Windows)                              │  │
│  │  - Cocoa/AppKit (macOS)                             │  │
│  │  - HTML5 Canvas (browser)                           │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                         │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │          Input Event Capture                         │  │
│  │  - Mouse events (move, click, scroll)               │  │
│  │  - Keyboard events (keypress, keyrelease)           │  │
│  │  - Window events (resize, move, close)              │  │
│  │  - Serialize & send to server                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Client Components Chi tiết

**1. Client Base Classes**
- `UIXpraClient`: Base cho GUI clients
- `WindowClient`: Window management mixin
- `ClientBaseClass`: Core functionality

**2. Platform-specific Implementations**

**GTK Client** (Primary - Linux)
```python
# xpra/client/gtk/client.py
class XpraClient(UIXpraClient, WindowClient):
    def make_client_window(self, wid, metadata):
        from xpra.client.gtk.window import ClientWindow
        return ClientWindow(self, wid, metadata)
```

**Qt6 Client** (Cross-platform)
```python
# xpra/client/qt6/client.py
class Qt6Client:
    windows: dict[int, QMainWindow] = {}
    
    def _process_new_window(self, packet):
        wid, x, y, w, h = packet[1:6]
        metadata = packet[6]
        window = ClientWindow(self, wid, x, y, w, h, metadata)
        self.windows[wid] = window
        window.show()
```

**Tk Client** (Lightweight)
```python
# xpra/client/tk/client.py
class XpraTkClient:
    def new_window(self, packet):
        window = ClientWindow(self, wid, ...)
        self.windows[wid] = window
```

**HTML5 Client** (Browser-based)
- JavaScript implementation
- WebSocket connection
- Canvas rendering
- All windows trong single canvas

### 3. Network Protocol Stack

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  Xpra Protocol (rencodeplus encoded packets)               │
│  ["new-window", wid, x, y, w, h, {...metadata}]           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               Presentation Layer                            │
│  - Compression: lz4 (default), brotli                      │
│  - Encryption: AES-256-GCM, SSL/TLS                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Session Layer                               │
│  - Framing: 8-byte header + payload                        │
│  - Chunking: Large data split into chunks                  │
│  - Flow control: damage-sequence acknowledgments           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                Transport Layer                              │
│  - TCP (reliable, ordered)                                 │
│  - QUIC (UDP-based, modern)                                │
│  - Unix domain sockets (local)                             │
│  - vsock (VM communication)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Tunnel/Wrapper (Optional)                      │
│  - SSH: ssh://user@host/                                   │
│  - SSL: ssl://host:port/                                   │
│  - WebSocket: ws://host:port/                              │
│  - HTTP Proxy                                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Window Creation Flow

```
SERVER                                          CLIENT
  │                                               │
  │ X11: New window appears                       │
  │                                               │
  ├─[Detect via XComposite]                      │
  │                                               │
  ├─[Assign WID=1]                               │
  │                                               │
  ├─[Capture window geometry & metadata]         │
  │                                               │
  ├────["new-window", 1, 100, 100, 800, 600, ───►│
  │     {"title": "xterm", ...}]                 │
  │                                               │
  │                                    [Parse packet]
  │                                               │
  │                              [Create QMainWindow/GtkWindow]
  │                                               │
  │                                  [Set title, position, size]
  │                                               │
  │                                         [window.show()]
  │                                               │
  │◄────["map-window", 1, True, ─────────────────┤
  │     {"screen": 0}]                           │
  │                                               │
  │ [Acknowledge window mapped]                   │
  │                                               │
```

### 2. Drawing/Rendering Flow

```
SERVER                                          CLIENT
  │                                               │
  │ X11: Window content changes                   │
  │                                               │
  ├─[XDamage notification]                       │
  │                                               │
  ├─[Capture damaged region]                     │
  │                                               │
  ├─[Encode pixels: rgb/h264/vp9]               │
  │                                               │
  ├─[Compress: lz4]                              │
  │                                               │
  ├────["draw", 1, 10, 20, 400, 300, ───────────►│
  │     "rgb", <data>, seq=123, ...]             │
  │                                               │
  │                                    [Decompress lz4]
  │                                               │
  │                                    [Decode rgb pixels]
  │                                               │
  │                              [Convert to native format]
  │                                               │
  │                                  [Blit to window canvas]
  │                                               │
  │                                       [window.update()]
  │                                               │
  │◄────["damage-sequence", 123, 1, ─────────────┤
  │     400, 300, decode_time, ""]               │
  │                                               │
  │ [Stats: decode took Xms]                      │
  │                                               │
```

### 3. Input Event Flow

```
CLIENT                                          SERVER
  │                                               │
  │ User clicks mouse in window                   │
  │                                               │
  ├─[Capture click event]                        │
  │                                               │
  ├─[Get window coordinates]                     │
  │                                               │
  ├────["button-action", 1, 1, True, ───────────►│
  │     [150, 200], {...modifiers}]              │
  │                                               │
  │                                   [Find window by WID=1]
  │                                               │
  │                             [Map to X11 window coords]
  │                                               │
  │                            [XTest inject mouse click]
  │                                               │
  │                              [X11 app receives click]
  │                                               │
  │                         [App redraws → new draw packet]
  │                                               │
  │◄────["draw", 1, ...]──────────────────────────┤
  │                                               │
```

## Threading Model

### Server Threading

```
┌──────────────────────────────────────────────────────────┐
│                    MAIN THREAD                           │
│  - GLib MainLoop                                         │
│  - Event dispatching                                     │
│  - Protocol packet routing                               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  NETWORK THREADS                         │
│  - Socket accept() (per listener)                       │
│  - Read/write (per connection)                          │
│  - Protocol parsing                                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  ENCODE THREADS                          │
│  - Pixel encoding (parallel)                            │
│  - Video encoding (hw accelerated)                      │
│  - Compression                                           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   DAMAGE THREAD                          │
│  - Monitor XDamage events                                │
│  - Schedule encoding                                     │
└──────────────────────────────────────────────────────────┘
```

### Client Threading

```
┌──────────────────────────────────────────────────────────┐
│                     UI THREAD                            │
│  - Native event loop (Qt/GTK/Win32)                     │
│  - Window management                                     │
│  - User input capture                                    │
│  - Rendering to screen                                   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                  NETWORK THREAD                          │
│  - Socket read/write                                     │
│  - Protocol parsing                                      │
│  - Packet deserialization                                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   DECODE QUEUE                           │
│  - Parallel decoding                                     │
│  - Video decoding (hw accelerated)                      │
│  - Pixel format conversion                               │
│  - Queue for UI thread                                   │
└──────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Observer Pattern
- Server monitors X11 events
- XDamage observers trigger encoding

### 2. Producer-Consumer Pattern
- Damage detection → encoding queue
- Network receive → decode queue
- Decode queue → render queue

### 3. Strategy Pattern
- Encoding strategies: rgb, png, jpeg, h264, vp9
- Auto-selection based on content type & network

### 4. Facade Pattern
- Protocol layer hides complexity
- Simple API: `send("packet-type", ...args)`

### 5. Factory Pattern
- Client window creation per platform
- Encoder/decoder selection

## Performance Optimizations

### Server Side

1. **Damage Batching**: Combine multiple small damages
2. **Smart Encoding**: Video for animations, image for static
3. **Hardware Acceleration**: NVENC, VAAPI, VideoToolbox
4. **Shared Memory**: MMAP for local connections
5. **Delta Encoding**: Send only changes

### Client Side

1. **OpenGL Rendering**: GPU-accelerated drawing
2. **Hardware Decoding**: Use GPU for video decode
3. **Draw Batching**: Combine updates before refresh
4. **Smart Refresh**: Skip invisible windows
5. **Async Decoding**: Don't block UI thread

---

**Next:** [Chi tiết Protocol](02-protocol.md)

