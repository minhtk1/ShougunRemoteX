# Rendering và Drawing trong Seamless Session

## Tổng quan Rendering Pipeline

```
┌───────────────────────────────────────────────────────────────┐
│                   SERVER SIDE PIPELINE                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  X11 Window                                                   │
│       ↓                                                       │
│  XDamage Event (region changed)                              │
│       ↓                                                       │
│  Capture Pixels (XComposite/XGetImage)                       │
│       ↓                                                       │
│  ┌─────────────────────────────────────────┐                │
│  │  Encoding Selection                      │                │
│  │  - Static content → PNG/JPEG             │                │
│  │  - Video/Animation → H264/VP9            │                │
│  │  - Text/UI → RGB with LZ4                │                │
│  └─────────────────┬───────────────────────┘                │
│                    ↓                                          │
│  Encode (parallel threads)                                    │
│       ↓                                                       │
│  Compress (lz4/brotli)                                       │
│       ↓                                                       │
│  Packetize                                                    │
│       ↓                                                       │
│  Send over network                                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                             │
                             │ Network
                             ↓
┌───────────────────────────────────────────────────────────────┐
│                   CLIENT SIDE PIPELINE                        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Receive packet                                               │
│       ↓                                                       │
│  Decompress (lz4/brotli)                                     │
│       ↓                                                       │
│  Parse packet                                                 │
│       ↓                                                       │
│  Queue to decode thread                                       │
│       ↓                                                       │
│  ┌─────────────────────────────────────────┐                │
│  │  Decode                                  │                │
│  │  - PNG/JPEG → PIL/Pillow                │                │
│  │  - H264/VP9 → FFmpeg/Hardware            │                │
│  │  - RGB → Direct copy                     │                │
│  └─────────────────┬───────────────────────┘                │
│                    ↓                                          │
│  Convert to native format (QImage/Pixbuf/BGRA)              │
│       ↓                                                       │
│  Blit to window surface                                       │
│       ↓                                                       │
│  Trigger window repaint                                       │
│       ↓                                                       │
│  Send damage-sequence ACK                                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Encoding Types

### 1. RGB/RGB24/RGB32

Raw pixel data, không compression (hoặc chỉ lz4).

**Khi dùng:**
- Text updates (terminal)
- Small regions
- When video codecs unavailable

**Format:**
```python
["draw", wid, x, y, width, height, "rgb24", 
 raw_pixels,  # width * height * 3 bytes
 sequence,
 rowstride,   # bytes per row = width * 3
 {}]

# Pixel order: RGBRGBRGB...
# Row 0: R G B R G B R G B ...
# Row 1: R G B R G B R G B ...
```

**Client decode:**
```python
def decode_rgb(data, width, height, rowstride):
    # Convert to native format
    if rowstride == width * 3:
        # Packed, direct use
        pixels = data
    else:
        # Need to unpack rows
        pixels = b""
        for y in range(height):
            row_start = y * rowstride
            row_end = row_start + (width * 3)
            pixels += data[row_start:row_end]
    
    # Create image
    # PIL: Image.frombytes("RGB", (width, height), pixels)
    # Qt: QImage(pixels, width, height, QImage.Format_RGB888)
    return pixels
```

### 2. PNG

Lossless compression, good for static content.

**Khi dùng:**
- Screenshots
- Static UI elements
- Fallback when video unavailable

**Format:**
```python
["draw", wid, x, y, width, height, "png",
 png_data,    # Standard PNG file format
 sequence,
 0,           # rowstride unused
 {}]
```

**Client decode:**
```python
from PIL import Image
import io

def decode_png(png_data, width, height):
    img = Image.open(io.BytesIO(png_data))
    
    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    return img
```

### 3. JPEG

Lossy compression, smaller size.

**Khi dùng:**
- Photos/images
- When quality loss acceptable
- Bandwidth limited

**Format:**
```python
["draw", wid, x, y, width, height, "jpeg",
 jpeg_data,   # Standard JPEG file format
 sequence,
 0,
 {"quality": 75}]  # 0-100
```

**Client decode:**
```python
def decode_jpeg(jpeg_data):
    img = Image.open(io.BytesIO(jpeg_data))
    return img
```

### 4. WebP

Modern format, better compression than JPEG.

**Khi dùng:**
- Alternative to JPEG/PNG
- When supported by both sides

**Format:**
```python
["draw", wid, x, y, width, height, "webp",
 webp_data,
 sequence,
 0,
 {"quality": 80, "lossless": False}]
```

### 5. H264

Video codec, excellent for animations.

**Khi dùng:**
- Video playback
- Smooth animations
- Scrolling content
- Screen sharing

**Format:**
```python
["draw", wid, x, y, width, height, "h264",
 h264_nal_units,  # H.264 NAL units
 sequence,
 0,
 {
     "frame": 123,          # Frame number in stream
     "profile": "baseline", # Profile level
     "level": "3.1",
     "csc": "YUV420P",      # Color space
 }]
```

**Server encoding:**
```python
# Using NVENC (NVIDIA GPU)
encoder = NvencEncoder(width, height, {
    "preset": "low-latency",
    "profile": "baseline",
    "bitrate": 2000000,  # 2 Mbps
})

# Feed frames
for frame_rgb in frames:
    h264_data = encoder.compress_image(frame_rgb)
    send_packet(["draw", ..., "h264", h264_data, ...])
```

**Client decoding:**
```python
# Using FFmpeg
import av

decoder = av.CodecContext.create("h264", "r")

def decode_h264_frame(h264_data):
    packet = av.Packet(h264_data)
    frames = decoder.decode(packet)
    
    if frames:
        frame = frames[0]
        # Convert to RGB
        img = frame.to_image()
        return img
```

**Hardware acceleration:**
```python
# NVIDIA (NVDEC)
decoder = NvdecDecoder()

# Intel (VAAPI)
decoder = VAAPIDecoder()

# AMD (AMF)
decoder = AMFDecoder()

# Apple (VideoToolbox)
decoder = VideoToolboxDecoder()
```

### 6. VP8/VP9

Google's video codecs, royalty-free.

**Khi dùng:**
- Alternative to H264
- Open-source preference
- Better quality at same bitrate (VP9)

**Format:**
```python
["draw", wid, x, y, width, height, "vp9",
 vp9_data,
 sequence,
 0,
 {"frame": 123, "quality": 80}]
```

### 7. AV1

Newest codec, best compression.

**Khi dùng:**
- When supported
- Bandwidth critical
- Best quality/size ratio

### 8. Scroll

Optimization for scrolling - copy existing pixels.

**Format:**
```python
["draw", wid, x, y, width, height, "scroll",
 "",           # No data needed
 sequence,
 0,
 {
     "scroll": (dx, dy),  # Scroll amount
     "flush": False,
 }]
```

**Client processing:**
```python
def process_scroll(self, wid, x, y, w, h, dx, dy):
    window = self.windows[wid]
    canvas = window.canvas
    
    # Copy existing pixels
    # canvas[x:x+w, y:y+h] = canvas[x-dx:x-dx+w, y-dy:y-dy+h]
    
    # Much faster than decoding full frame!
```

## Draw Packet Structure

### Complete Draw Packet

```python
[
    "draw",              # Packet type
    wid,                 # Window ID
    x, y,                # Position of region
    width, height,       # Size of region
    coding,              # Encoding type
    data,                # Encoded pixel data
    packet_sequence,     # Sequence number
    rowstride,           # Bytes per row (0 if N/A)
    options,             # Additional options dict
]
```

### Options Dictionary

```python
options = {
    # Quality settings
    "quality": 80,           # 0-100 for lossy codecs
    "speed": 50,             # Encode speed vs quality
    
    # Video specific
    "frame": 123,            # Frame number in video stream
    "profile": "baseline",   # Codec profile
    "csc": "YUV420P",       # Color space conversion
    
    # Metadata
    "lz4": True,            # Was compressed with lz4?
    "flush": True,          # Last packet in batch?
    "eos": False,           # End of stream?
    
    # Timing
    "timestamp": 1234567,   # Server timestamp
    "elapsed": 15,          # Encode time in ms
}
```

## Damage Tracking

### Server Side: XDamage

```python
# X11 notifies server of damaged regions
def handle_xdamage_event(event):
    window = event.window
    region = event.region  # (x, y, width, height)
    
    # Add to damage queue
    damage_queue.append((window, region))

# Batch damages
def process_damage_queue():
    damages = {}
    
    # Group by window
    for window, region in damage_queue:
        if window not in damages:
            damages[window] = []
        damages[window].append(region)
    
    # Merge overlapping regions
    for window, regions in damages.items():
        merged = merge_regions(regions)
        
        for region in merged:
            encode_and_send(window, region)
```

### Region Merging

```python
def merge_regions(regions):
    """Merge overlapping/adjacent regions"""
    if not regions:
        return []
    
    # Sort by position
    regions = sorted(regions, key=lambda r: (r[1], r[0]))
    
    merged = [regions[0]]
    
    for current in regions[1:]:
        last = merged[-1]
        
        # Check if overlaps or adjacent
        if rectangles_intersect(last, current):
            # Merge
            merged[-1] = merge_rectangles(last, current)
        else:
            merged.append(current)
    
    return merged

def rectangles_intersect(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    
    # Check if adjacent (within threshold)
    threshold = 10
    
    return not (x1 + w1 + threshold < x2 or  # r1 left of r2
                x2 + w2 + threshold < x1 or  # r2 left of r1
                y1 + h1 + threshold < y2 or  # r1 above r2
                y2 + h2 + threshold < y1)    # r2 above r1

def merge_rectangles(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    
    x = min(x1, x2)
    y = min(y1, y2)
    w = max(x1 + w1, x2 + w2) - x
    h = max(y1 + h1, y2 + h2) - y
    
    return (x, y, w, h)
```

## Encoding Selection Strategy

### Auto-Selection Logic

```python
def select_encoding(window, region, content_type, network_state):
    width, height = region[2:4]
    area = width * height
    
    # Content analysis
    if content_type == "video":
        return "h264" if has_hardware_encoder else "png"
    
    if content_type == "text":
        return "rgb" if area < 10000 else "png"
    
    # Network considerations
    if network_state.bandwidth < 1_000_000:  # < 1 Mbps
        if has_video_encoder:
            return "h264"
        else:
            return "jpeg" if area > 50000 else "png"
    
    # Default for good network
    if area > 100000:  # Large region
        return "h264" if has_video_encoder else "png"
    else:
        return "rgb" if area < 10000 else "png"
```

### Content Type Detection

```python
def detect_content_type(pixels, previous_frame):
    if previous_frame is None:
        return "static"
    
    # Calculate difference
    diff = pixel_difference(pixels, previous_frame)
    
    if diff < 0.01:  # < 1% changed
        return "static"
    elif diff < 0.1:  # < 10% changed
        return "text"
    else:
        return "video"

def pixel_difference(frame1, frame2):
    """Calculate percentage of different pixels"""
    diff_pixels = sum(1 for a, b in zip(frame1, frame2) if a != b)
    total_pixels = len(frame1)
    return diff_pixels / total_pixels
```

## Client Side Rendering

### Decode Thread

```python
from queue import Queue
from threading import Thread

class DecodeQueue:
    def __init__(self, client):
        self.client = client
        self.queue = Queue()
        self.thread = Thread(target=self.decode_loop, daemon=True)
        self.thread.start()
    
    def add_draw_packet(self, packet):
        self.queue.put(packet)
    
    def decode_loop(self):
        while True:
            packet = self.queue.get()
            
            try:
                decoded = self.decode_packet(packet)
                
                # Queue to UI thread for rendering
                self.client.render_queue.put(decoded)
            except Exception as e:
                print(f"Decode error: {e}")
    
    def decode_packet(self, packet):
        wid, x, y, w, h = packet[1:6]
        coding = packet[6]
        data = packet[7]
        sequence = packet[8]
        
        start = time.time()
        
        # Decode based on encoding
        if coding == "rgb":
            img = self.decode_rgb(data, w, h)
        elif coding == "png":
            img = self.decode_png(data)
        elif coding == "jpeg":
            img = self.decode_jpeg(data)
        elif coding == "h264":
            img = self.decode_h264(data)
        elif coding == "scroll":
            img = None  # Special handling
        else:
            raise ValueError(f"Unknown encoding: {coding}")
        
        decode_time = int((time.time() - start) * 1000)
        
        return {
            "wid": wid,
            "region": (x, y, w, h),
            "image": img,
            "sequence": sequence,
            "decode_time": decode_time,
        }
```

### Render to Window

#### Qt Implementation

```python
class ClientWindow(QMainWindow):
    def draw(self, x, y, width, height, coding, data, rowstride):
        """Render decoded image to window"""
        if coding == "scroll":
            self.scroll(data["dx"], data["dy"])
            return
        
        # Decode image
        img = self.decode_image(coding, data, width, height)
        
        # Convert to QPixmap
        if isinstance(img, bytes):
            # Raw RGB data
            qimg = QImage(img, width, height, 
                         rowstride or width * 3,
                         QImage.Format_RGB888)
        else:
            # PIL Image
            qimg = ImageQt.ImageQt(img)
        
        # Draw to canvas
        painter = QPainter(self.canvas)
        painter.drawImage(x, y, qimg)
        painter.end()
        
        # Update display
        self.label.setPixmap(self.canvas)
        self.label.update(x, y, width, height)
```

#### GTK Implementation

```python
class ClientWindow(Gtk.Window):
    def draw(self, x, y, width, height, coding, data):
        # Decode to Pixbuf
        pixbuf = self.decode_to_pixbuf(coding, data, width, height)
        
        # Composite onto backing pixbuf
        pixbuf.composite(
            self.backing,
            x, y, width, height,
            x, y,
            1.0, 1.0,  # Scale
            GdkPixbuf.InterpType.NEAREST,
            255  # Alpha
        )
        
        # Trigger redraw
        self.drawing_area.queue_draw_area(x, y, width, height)
    
    def on_draw(self, widget, cr):
        """GTK draw callback"""
        # Paint backing pixbuf to Cairo context
        Gdk.cairo_set_source_pixbuf(cr, self.backing, 0, 0)
        cr.paint()
```

### OpenGL Rendering (Optional)

For better performance:

```python
class GLClientWindow:
    def __init__(self):
        self.gl_context = create_gl_context()
        self.texture = create_gl_texture()
    
    def draw(self, x, y, width, height, pixels):
        # Upload to GPU texture
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexSubImage2D(
            GL_TEXTURE_2D, 0,
            x, y, width, height,
            GL_RGB, GL_UNSIGNED_BYTE,
            pixels
        )
        
        # Render textured quad
        self.render_quad(x, y, width, height)
```

## Acknowledgment

### Send damage-sequence

```python
def send_damage_ack(self, sequence, wid, width, height, decode_time, error=""):
    self.send("damage-sequence",
             sequence,
             wid,
             width, height,
             decode_time,  # milliseconds
             error)        # Empty string if OK
```

### Server processes acknowledgments

```python
def _process_damage_sequence(self, proto, packet):
    sequence = packet[1]
    wid = packet[2]
    width, height = packet[3:5]
    decode_time = packet[5]
    error = packet[6] if len(packet) > 6 else ""
    
    if error:
        log.warn(f"Client decode error for {sequence}: {error}")
        # Maybe fallback to simpler encoding
    
    # Record statistics
    self.record_decode_time(wid, decode_time)
    
    # Adjust encoding based on decode time
    if decode_time > 50:  # > 50ms is slow
        self.decrease_quality(wid)
    elif decode_time < 10:  # < 10ms is fast
        self.increase_quality(wid)
```

## Performance Optimization

### 1. Parallel Encoding

```python
from concurrent.futures import ThreadPoolExecutor

encoder_pool = ThreadPoolExecutor(max_workers=4)

def encode_regions_parallel(regions):
    futures = []
    
    for region in regions:
        future = encoder_pool.submit(encode_region, region)
        futures.append(future)
    
    # Wait for all
    results = [f.result() for f in futures]
    return results
```

### 2. Encoding Cache

```python
class EncodingCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, window, region, pixels):
        # Hash pixels
        key = hash(pixels)
        
        if key in self.cache:
            return self.cache[key]
        
        # Encode
        encoded = encode(pixels)
        self.cache[key] = encoded
        
        # Limit cache size
        if len(self.cache) > 100:
            self.cache.pop(next(iter(self.cache)))
        
        return encoded
```

### 3. Smart Batching

```python
class DamageBatcher:
    def __init__(self, delay_ms=10):
        self.delay = delay_ms / 1000.0
        self.pending = []
        self.timer = None
    
    def add_damage(self, damage):
        self.pending.append(damage)
        
        if self.timer is None:
            self.timer = Timer(self.delay, self.flush)
            self.timer.start()
    
    def flush(self):
        if self.pending:
            # Merge and encode all pending damages
            merged = merge_regions(self.pending)
            encode_and_send(merged)
            self.pending.clear()
        
        self.timer = None
```

---

**Next:** [Hướng dẫn Implementation](06-implementation.md)

