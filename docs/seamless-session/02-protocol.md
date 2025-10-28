# Chi tiết Protocol Xpra

## Tổng quan Protocol

Xpra sử dụng một protocol tùy chỉnh được thiết kế để:
- **Low latency**: Minimize overhead
- **Efficient**: Compression & encoding thông minh
- **Flexible**: Support nhiều transport layers
- **Secure**: Built-in encryption

## Packet Structure

### 1. Packet Format

Mỗi packet bao gồm 2 phần: **Header** (8 bytes) + **Payload** (variable)

```
┌─────────────────────────────────────────────────────────┐
│                    XPRA PACKET                          │
├─────────────────────────────────────────────────────────┤
│  HEADER (8 bytes)                                       │
│  ┌──────┬──────────┬────────┬────────┬───────────────┐ │
│  │  'P' │  Flags   │ Comp.  │ Chunk  │ Payload Size  │ │
│  │ (1B) │   (1B)   │  (1B)  │  (1B)  │    (4B)       │ │
│  └──────┴──────────┴────────┴────────┴───────────────┘ │
├─────────────────────────────────────────────────────────┤
│  PAYLOAD (variable length)                              │
│  - Encoded with rencodeplus                             │
│  - Optionally compressed (lz4/brotli)                   │
│  - Optionally encrypted (AES)                           │
│  - Format: [packet_type, arg1, arg2, ...]              │
└─────────────────────────────────────────────────────────┘
```

### 2. Header Chi tiết

#### Byte 0: Magic Byte
```
Value: 'P' (0x50)
Purpose: Packet identification
```

#### Byte 1: Protocol Flags (Bitmask)
```
Bit 4 (16): rencodeplus encoding [REQUIRED]
Bit 3 (8):  flush flag (no more packets immediately following)
Bit 1 (2):  cipher flag (AES encrypted)

Examples:
  16 (0x10) = rencodeplus only
  24 (0x18) = rencodeplus + flush
  18 (0x12) = rencodeplus + cipher
  26 (0x1A) = rencodeplus + cipher + flush
```

#### Byte 2: Compression Level
```
High 4 bits: Compressor type
  0x10 (16) = lz4
  0x40 (64) = brotli
  
Low 4 bits: Compression level (0-15)
  0 = no compression
  1-9 = compression levels

Examples:
  0x00 = No compression
  0x15 = lz4 level 5
  0x43 = brotli level 3
```

#### Byte 3: Chunk Index
```
0 = Main packet
1-255 = Chunk data (for large payloads)

Purpose: Send large data efficiently
- Chunk 1,2,3... = binary data
- Chunk 0 (main) = packet with placeholder
```

#### Bytes 4-7: Payload Size
```
4-byte unsigned integer (big-endian)
Maximum: 2^32 - 1 = 4,294,967,295 bytes (~4GB)
Typical: 100 bytes (control) to 1MB (frame data)
```

### 3. Payload Format

#### Rencodeplus Encoding

Rencodeplus là custom serialization format của Xpra, similar to rencode/bencode nhưng được optimize.

**Supported Types:**
```python
- Integers: variable length encoding
- Strings: UTF-8 encoded
- Bytes: raw binary data
- Lists: [item1, item2, ...]
- Tuples: (item1, item2, ...)
- Dictionaries: {key: value, ...}
- Booleans: True, False
- None (avoid if possible)
```

**Packet Structure:**
```python
[packet_type, arg1, arg2, arg3, ...]

# Examples:
["hello", {"version": "6.3.0", "platform": "linux"}]
["new-window", 1, 100, 100, 800, 600, {"title": "xterm"}]
["draw", 1, 0, 0, 800, 600, "rgb", b"...", 123, 2400]
["lost-window", 1]
```

## Core Packet Types

### 1. Connection & Handshake

#### hello
```python
["hello", capabilities_dict]

# Client → Server
["hello", {
    "version": "6.3.0",
    "platform": "win32",
    "username": "user",
    "uuid": "abc-123",
    "encodings": ["h264", "vp9", "png", "rgb"],
    "windows": True,
    "keyboard": True,
    "clipboard": True,
    "audio": True,
    ...
}]

# Server → Client
["hello", {
    "version": "6.3.0",
    "platform": "linux",
    "display": ":100",
    "windows": True,
    "encodings.core": ["rgb", "png", "jpeg"],
    "encodings.with_quality": ["jpeg", "webp"],
    "encodings.with_speed": ["h264", "vp9"],
    ...
}]
```

#### challenge
```python
# Server → Client (if authentication required)
["challenge", challenge_data, digest_type]

# Example
["challenge", b"random_bytes_123", "hmac+sha256"]
```

#### challenge-response  
```python
# Client → Server
["challenge-response", response_data]

# Example with HMAC
["challenge-response", hmac_hash]
```

#### disconnect
```python
["disconnect", reason]

# Examples
["disconnect", "connection lost"]
["disconnect", "session terminated"]
```

### 2. Window Management

#### new-window
```python
["new-window", wid, x, y, width, height, metadata]

# Example
["new-window", 1, 100, 100, 800, 600, {
    "title": "Terminal - user@host",
    "class-instance": ("xterm", "XTerm"),
    "pid": 12345,
    "window-type": ["NORMAL"],
    "size-constraints": {
        "minimum-size": (80, 24),
        "base-size": (0, 0),
    },
    "has-alpha": False,
}]
```

#### new-override-redirect
```python
["new-override-redirect", wid, x, y, width, height, metadata]

# For menus, tooltips, dropdowns
# Similar to new-window but without decorations
```

#### lost-window
```python
["lost-window", wid]

# Example
["lost-window", 1]
```

#### window-metadata
```python
["window-metadata", wid, metadata]

# Examples
["window-metadata", 1, {"title": "New Title"}]
["window-metadata", 1, {"size-hints": {...}}]
["window-metadata", 1, {"icon": image_data}]
```

#### map-window
```python
# Client → Server: Window is now mapped
["map-window", wid, x, y, width, height, props]

# Example
["map-window", 1, 100, 100, 800, 600, {
    "screen": 0,
    "fullscreen": False,
}]
```

#### unmap-window
```python
# Client → Server: Window is hidden/unmapped
["unmap-window", wid]
```

#### configure-window
```python
# Client → Server: Window moved/resized
["configure-window", wid, x, y, width, height, props]

# Example
["configure-window", 1, 200, 150, 1024, 768, {}]
```

#### close-window
```python
# Client → Server: User wants to close window
["close-window", wid]
```

#### raise-window
```python
# Server → Client: Bring window to front
["raise-window", wid]
```

#### focus
```python
# Client → Server: Focus changed
["focus", wid, modifiers]

# Examples
["focus", 1, []]          # Focus window 1
["focus", 0, []]          # Unfocus all
```

### 3. Drawing & Rendering

#### draw
```python
["draw", wid, x, y, width, height, coding, data, packet_sequence, 
 rowstride, options]

# Example: RGB data
["draw", 1, 0, 0, 800, 600, "rgb", 
 b"\xFF\x00\x00...",  # Raw RGB pixels
 12345,                # Sequence number
 2400,                 # Bytes per row (800 * 3)
 {}]                   # Options

# Example: H264 video frame
["draw", 1, 0, 0, 800, 600, "h264",
 b"\x00\x00\x00\x01...",  # H264 NAL units
 12346,
 0,                        # Not used for video
 {"frame": 123, "profile": "baseline"}]

# Example: PNG image
["draw", 1, 100, 100, 400, 300, "png",
 b"\x89PNG\r\n...",
 12347,
 0,
 {}]
```

**Encoding Types:**
- `rgb`, `rgb24`, `rgb32`: Raw RGB pixels
- `png`: PNG compressed image
- `jpeg`: JPEG compressed image
- `webp`: WebP compressed image
- `h264`: H.264 video stream
- `vp8`, `vp9`: VP8/VP9 video stream
- `av1`: AV1 video stream
- `scroll`: Scroll optimization

#### damage-sequence
```python
# Client → Server: Acknowledge draw packet processed
["damage-sequence", packet_sequence, wid, width, height, 
 decode_time, message]

# Example
["damage-sequence", 12345, 1, 800, 600, 15, ""]
#                   ^       ^  ^    ^    ^   ^
#                   seq     wid w   h    ms  error

# With error
["damage-sequence", 12345, 1, 800, 600, -1, "decode failed"]
```

#### eos
```python
# Server → Client: End of stream for video encoding
["eos", wid, coding]

# Example
["eos", 1, "h264"]
```

### 4. Input Events

#### button-action
```python
# Client → Server: Mouse button click
["button-action", wid, button, pressed, pointer, modifiers, buttons]

# Example
["button-action", 1, 1, True, (150, 200), ["shift"], [1]]
#                 ^  ^  ^     ^           ^           ^
#                wid btn down (x,y)      mods        pressed_btns
```

#### pointer-position
```python
# Client → Server: Mouse moved
["pointer-position", wid, pointer, modifiers, buttons]

# Example
["pointer-position", 1, (150, 200), [], []]
```

#### key-action
```python
# Client → Server: Keyboard key press/release
["key-action", wid, keyname, pressed, modifiers, keyval, 
 string, keycode, group]

# Example
["key-action", 1, "a", True, [], 97, "a", 38, 0]
["key-action", 1, "Return", True, [], 65293, "", 36, 0]
["key-action", 1, "Control_L", True, ["control"], 65507, "", 37, 0]
```

#### wheel-motion
```python
# Client → Server: Mouse wheel scroll
["wheel-motion", wid, deltax, deltay, pointer, modifiers]

# Example
["wheel-motion", 1, 0.0, -1.0, (150, 200), []]
#                ^  ^     ^     ^           ^
#               wid dx    dy   (x,y)       mods
```

### 5. Additional Features

#### sound-data
```python
# Server → Client: Audio data
["sound-data", codec, data, metadata, sequence]

# Example
["sound-data", "opus", b"...", 
 {"channels": 2, "sample_rate": 48000}, 123]
```

#### clipboard-token
```python
# Clipboard ownership notification
["clipboard-token", selection, target, data]
```

#### notification-show
```python
# Server → Client: Show notification
["notification-show", nid, app_name, replaces_id, app_icon,
 summary, body, actions, hints, timeout, icon_data]
```

#### ping
```python
# Keep-alive packet
["ping", timestamp]

# Response
["ping_echo", timestamp, client_timestamp, will_timeout_in]
```

#### info-request
```python
# Request system information
["info-request", [categories]]

# Response
["info-response", {...}]
```

## Packet Chunking

Để gửi data lớn (VD: 4K frame = 32MB raw), Xpra sử dụng chunking:

```python
# Example: Send large RGB frame

# Step 1: Send chunks with index > 0
chunk_data_1 = pixels[0:10MB]
send_packet_with_chunk_index(chunk_data_1, chunk_index=1)

chunk_data_2 = pixels[10MB:20MB]
send_packet_with_chunk_index(chunk_data_2, chunk_index=2)

chunk_data_3 = pixels[20MB:30MB]
send_packet_with_chunk_index(chunk_data_3, chunk_index=3)

# Step 2: Send main packet (chunk_index=0) with placeholder
main_packet = ["draw", 1, 0, 0, 3840, 2160, "rgb", 
               "",  # Empty placeholder (will be replaced with chunk 1)
               12345, 11520, {}]
send_packet_with_chunk_index(main_packet, chunk_index=0)

# Receiver reassembles:
# packet[7] = chunk_1 + chunk_2 + chunk_3
```

## Compression

### LZ4 (Default)
```python
- Fast compression/decompression
- Good for real-time
- Typical ratio: 2-4x
- Used for: control packets, some pixel data
```

### Brotli
```python
- Better compression ratio
- Slower than lz4
- Typical ratio: 4-8x
- Used for: static content, large metadata
```

### None
```python
- Already compressed data (jpeg, png, h264)
- Small packets (overhead > gain)
- Low-latency critical packets
```

## Encryption

### AES-256-GCM
```python
# Cipher flag = True in header
# Payload is encrypted after encoding/compression

Key derivation: PBKDF2 from password
IV: Random per packet
Authentication: GCM tag
```

### SSL/TLS
```python
# Applied at transport layer, not packet layer
# Encrypts entire connection
# Certificate-based authentication
```

## Packet Aliases

Để giảm bandwidth, sau khi handshake, server gửi alias mapping:

```python
# In hello capabilities
"aliases": {
    1: "new-window",
    2: "lost-window", 
    3: "draw",
    4: "window-metadata",
    ...
}

# Subsequent packets can use integer instead of string
[3, 1, 0, 0, 800, 600, "rgb", ...]  # Instead of ["draw", ...]
```

## Flow Control

### Damage Sequence Acknowledgment

```
SERVER                          CLIENT
  │                               │
  ├──["draw", ..., seq=100]──────►│
  │                               ├─[Decode & render]
  │◄──["damage-sequence", 100]───┤
  │                               │
  ├──["draw", ..., seq=101]──────►│
  │                               ├─[Decode & render]
  │◄──["damage-sequence", 101]───┤
```

Server tracks:
- Which sequences are acknowledged
- Decode time statistics
- Adjust encoding quality/speed based on stats

### Congestion Control

```python
# Server monitors:
- Network latency (ping times)
- Decode times (from damage-sequence)
- Packet queue sizes

# Auto-adjust:
- Encoding quality (lower quality if slow)
- Encoding speed preset (faster preset if lagging)
- Frame rate (skip frames if needed)
- Batch size (batch more damages if high latency)
```

## Example: Complete Window Creation Sequence

```python
# 1. Server detects new X11 window
# 2. Server assigns WID=1

# 3. Server → Client: New window notification
["new-window", 1, 100, 100, 800, 600, {
    "title": "xterm",
    "class-instance": ("xterm", "XTerm"),
    "size-constraints": {...},
}]

# 4. Client creates native window
# 5. Client → Server: Window mapped
["map-window", 1, 100, 100, 800, 600, {"screen": 0}]

# 6. Server captures initial window content
# 7. Server → Client: Draw initial frame
["draw", 1, 0, 0, 800, 600, "png", b"...", 1, 0, {}]

# 8. Client decodes and renders
# 9. Client → Server: Acknowledge
["damage-sequence", 1, 1, 800, 600, 12, ""]

# 10. User types 'ls' in xterm
# 11. Client → Server: Key events
["key-action", 1, "l", True, [], 108, "l", 46, 0]
["key-action", 1, "l", False, [], 108, "l", 46, 0]
["key-action", 1, "s", True, [], 115, "s", 39, 0]
["key-action", 1, "s", False, [], 115, "s", 39, 0]

# 12. Terminal updates display
# 13. Server → Client: Draw updated region
["draw", 1, 0, 480, 800, 120, "rgb", b"...", 2, 2400, {}]

# 14. Client renders update
# 15. Client → Server: Acknowledge
["damage-sequence", 2, 1, 800, 120, 8, ""]
```

---

**Next:** [Quy trình kết nối](03-connection.md)

