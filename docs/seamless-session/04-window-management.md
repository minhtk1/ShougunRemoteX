# Quản lý Windows trong Seamless Session

## Tổng quan Window Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│              WINDOW LIFECYCLE                            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Server: App creates X11 window                          │
│           ↓                                              │
│  Server: Detect new window (XComposite)                  │
│           ↓                                              │
│  Server: Assign unique WID                               │
│           ↓                                              │
│  Server → Client: Send "new-window" packet              │
│           ↓                                              │
│  Client: Create native window (Qt/GTK/Win32)            │
│           ↓                                              │
│  Client: Show window on screen                           │
│           ↓                                              │
│  Client → Server: Send "map-window" packet              │
│           ↓                                              │
│  ┌────────────────────────────────┐                     │
│  │   ACTIVE WINDOW STATE          │                     │
│  │  - User interactions           │                     │
│  │  - Content updates (draw)      │                     │
│  │  - Metadata changes            │                     │
│  │  - Window operations           │                     │
│  └────────────────────────────────┘                     │
│           ↓                                              │
│  Server/Client: Window close request                     │
│           ↓                                              │
│  Server → Client: Send "lost-window" packet             │
│           ↓                                              │
│  Client: Destroy native window                           │
│           ↓                                              │
│  Server: Cleanup WID resources                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Window Identification

### Window ID (WID)

Mỗi window được identify bằng **Window ID (WID)** duy nhất:

```python
# Server side
class WindowServer:
    def __init__(self):
        self._id_to_window = {}  # wid → window_model
        self._window_to_id = {}  # window_model → wid
        self._next_wid = 1
    
    def assign_wid(self, window_model):
        wid = self._next_wid
        self._next_wid += 1
        
        self._id_to_window[wid] = window_model
        self._window_to_id[window_model] = wid
        
        return wid

# Client side
class XpraClient:
    def __init__(self):
        self.windows = {}  # wid → native_window
```

**WID characteristics:**
- Integer, starts from 1
- Unique per session
- Không reuse (even after window closed)
- Dùng để refer to window trong tất cả packets

## Window Types

### 1. Normal Windows

Regular application windows với decorations (title bar, borders):

```python
["new-window", wid, x, y, width, height, {
    "window-type": ["NORMAL"],
    "decorations": True,
}]
```

### 2. Override-Redirect Windows

Special windows without window manager control (menus, tooltips, dropdowns):

```python
["new-override-redirect", wid, x, y, width, height, {
    "override-redirect": True,
}]
```

**Characteristics:**
- No title bar, no borders
- Always on top
- No window manager decorations
- Used for: popup menus, tooltips, combo box dropdowns

### 3. Modal Windows

Windows that block interaction with parent:

```python
["new-window", wid, x, y, width, height, {
    "modal": True,
    "transient-for": parent_wid,
}]
```

### 4. Transient Windows

Temporary windows related to parent (dialogs):

```python
["new-window", wid, x, y, width, height, {
    "transient-for": parent_wid,
}]
```

## Window Metadata

### Complete Metadata Structure

```python
metadata = {
    # Basic info
    "title": "Terminal - user@host",
    "class-instance": ("xterm", "XTerm"),  # (instance, class)
    "command": "/usr/bin/xterm",
    "pid": 12345,
    "workspace": 0,
    
    # Window type
    "window-type": ["NORMAL"],  # NORMAL, DIALOG, SPLASH, UTILITY, etc.
    "override-redirect": False,
    
    # Decorations
    "decorations": True,
    
    # Parent/child relationships
    "transient-for": None,  # Parent WID if dialog
    "modal": False,
    "group-leader": 123,    # Window group
    
    # Size constraints
    "size-constraints": {
        "minimum-size": (80, 24),      # Min width, height
        "maximum-size": (2000, 2000),  # Max width, height
        "base-size": (0, 0),           # Base size for resize
        "increment": (1, 1),           # Resize step
        "minimum-aspect": (1, 1),      # Min aspect ratio
        "maximum-aspect": (16, 9),     # Max aspect ratio
    },
    
    # Position hints
    "set-initial-position": True,
    "requested-position": (100, 100),
    
    # State
    "iconic": False,           # Minimized?
    "fullscreen": False,
    "maximized": False,
    "above": False,            # Always on top?
    "below": False,            # Always on bottom?
    "shaded": False,           # Rolled up?
    "skip-taskbar": False,
    "skip-pager": False,
    "sticky": False,           # On all workspaces?
    "focused": False,
    
    # Visual
    "has-alpha": False,        # Transparency support?
    "opacity": 100,            # 0-100
    "frame-extents": (0, 0, 0, 0),  # left, right, top, bottom
    
    # Icons
    "icon": png_encoded_data,  # Window icon
    "icons": {                 # Multiple sizes
        "16x16": icon_16_data,
        "32x32": icon_32_data,
        "64x64": icon_64_data,
    },
    
    # Input
    "input-only": False,
    "bypass-compositor": False,
    
    # X11 specific
    "xid": 0x1234567,         # X11 window ID
    "shape": None,            # Non-rectangular shape data
    
    # Protocols supported
    "protocols": ["WM_DELETE_WINDOW", "WM_TAKE_FOCUS"],
    
    # Custom properties
    "application-id": "org.xterm.XTerm",
    "gtk-application-id": "org.gnome.Terminal",
}
```

## Window Creation

### Server Side: Detect & Send

```python
# xpra/server/source/windows.py
class WindowsMixin:
    def new_window(self, ptype, wid, window, x, y, w, h, client_properties):
        """Send new window to client"""
        # Get window metadata
        metadata = self.make_window_metadata(window)
        
        # Add client-specific properties
        metadata.update(client_properties)
        
        # Build packet
        packet = [ptype, wid, x, y, w, h, metadata]
        
        # Send to client
        self.send_async(packet)
        
        # Track window state
        self.window_sources[wid] = WindowSource(
            self, wid, window, ...
        )
```

### Client Side: Create Native Window

#### Qt6 Implementation

```python
# xpra/client/qt6/window.py
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt

class ClientWindow(QMainWindow):
    def __init__(self, client, wid, x, y, w, h, metadata):
        super().__init__()
        
        self.client = client
        self.wid = wid
        self.metadata = metadata
        
        # Set window properties
        self.setWindowTitle(metadata.get("title", ""))
        
        # Override-redirect windows
        if metadata.get("override-redirect"):
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.Window | 
                Qt.WindowType.X11BypassWindowManagerHint
            )
        
        # Modal windows
        if metadata.get("modal"):
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Transient-for (dialog parent)
        if "transient-for" in metadata:
            parent_wid = metadata["transient-for"]
            parent_window = client.windows.get(parent_wid)
            if parent_window:
                self.setParent(parent_window)
        
        # Set size and position
        self.move(x, y)
        self.resize(w, h)
        
        # Size constraints
        if "size-constraints" in metadata:
            sc = metadata["size-constraints"]
            if "minimum-size" in sc:
                min_w, min_h = sc["minimum-size"]
                self.setMinimumSize(min_w, min_h)
            if "maximum-size" in sc:
                max_w, max_h = sc["maximum-size"]
                self.setMaximumSize(max_w, max_h)
        
        # Create drawing area
        self.canvas = QPixmap(w, h)
        self.canvas.fill(Qt.GlobalColor.white)
        
        self.label = QLabel()
        self.label.setPixmap(self.canvas)
        self.setCentralWidget(self.label)
        
        # Install event handlers
        self.installEventFilter(self)
    
    def show(self):
        """Show window and notify server"""
        super().show()
        
        # Send map-window to server
        self.client.send("map-window", 
                        self.wid, 
                        self.x(), self.y(), 
                        self.width(), self.height(), 
                        {"screen": 0})
```

#### GTK Implementation

```python
# xpra/client/gtk/window.py
from gi.repository import Gtk, Gdk

class ClientWindow(Gtk.Window):
    def __init__(self, client, wid, metadata):
        super().__init__()
        
        self.client = client
        self.wid = wid
        self.metadata = metadata
        
        # Set properties
        self.set_title(metadata.get("title", ""))
        
        # Window type
        window_type = metadata.get("window-type", ["NORMAL"])[0]
        if window_type == "DIALOG":
            self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        elif window_type == "UTILITY":
            self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        
        # Override-redirect
        if metadata.get("override-redirect"):
            self.set_decorated(False)
            self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        
        # Modal
        if metadata.get("modal"):
            self.set_modal(True)
        
        # Transient-for
        if "transient-for" in metadata:
            parent_wid = metadata["transient-for"]
            parent = client.windows.get(parent_wid)
            if parent:
                self.set_transient_for(parent)
        
        # Drawing area
        self.drawing_area = Gtk.DrawingArea()
        self.add(self.drawing_area)
        
        # Connect signals
        self.connect("delete-event", self.on_delete)
        self.connect("configure-event", self.on_configure)
        self.drawing_area.connect("draw", self.on_draw)
```

## Window Operations

### Move & Resize

```python
# Client → Server: User moved/resized window
["configure-window", wid, x, y, width, height, {
    "resize-counter": 123,  # Track resize sequence
}]

# Server processes:
def _process_configure_window(self, proto, packet):
    wid, x, y, w, h, props = packet[1:7]
    
    window_source = self.window_sources.get(wid)
    if window_source:
        # Update window geometry
        window_source.move_resize(x, y, w, h)
        
        # Acknowledge
        self.send_async("configure-override-redirect" if or_window 
                       else "configure-window", 
                       wid, x, y, w, h)
```

### Raise/Lower

```python
# Server → Client: Bring window to front
["raise-window", wid]

# Client processes:
def _process_raise_window(self, packet):
    wid = packet[1]
    window = self.windows.get(wid)
    if window:
        window.raise_()  # Qt
        # or window.present() for GTK
```

### Focus Management

```python
# Client → Server: Focus changed
["focus", wid, modifiers]

# Server processes:
def _process_focus(self, proto, packet):
    wid = packet[1]
    modifiers = packet[2]
    
    # Set X11 focus
    if wid > 0:
        window = self._id_to_window.get(wid)
        if window:
            window.set_input_focus()
    else:
        # wid=0 means unfocus all
        self.clear_focus()
```

### Minimize/Maximize/Fullscreen

```python
# Client → Server: State change request
["window-state", wid, state_changes]

# Examples
["window-state", 1, {"maximized": True}]
["window-state", 1, {"fullscreen": True}]
["window-state", 1, {"iconic": True}]  # Minimize

# Server → Client: State changed
["window-metadata", wid, {"maximized": True}]
```

### Close Window

```python
# Client → Server: User clicked close button
["close-window", wid]

# Server processes:
def _process_close_window(self, proto, packet):
    wid = packet[1]
    window = self._id_to_window.get(wid)
    
    if window:
        # Send WM_DELETE_WINDOW to app
        if "WM_DELETE_WINDOW" in window.get_protocols():
            window.send_client_message("WM_DELETE_WINDOW")
        else:
            # Force close
            window.destroy()

# When X11 window actually closes:
# Server → Client
["lost-window", wid]

# Client processes:
def _process_lost_window(self, packet):
    wid = packet[1]
    window = self.windows.pop(wid, None)
    if window:
        window.close()
        window.destroy()
```

## Window Properties Updates

### Metadata Updates

```python
# Server → Client: Property changed
["window-metadata", wid, changes]

# Examples:

# Title changed
["window-metadata", 1, {"title": "New Title"}]

# Icon changed
["window-metadata", 1, {"icon": png_data}]

# Size hints changed
["window-metadata", 1, {
    "size-constraints": {
        "minimum-size": (100, 100),
    }
}]
```

### Client Handling

```python
def _process_window_metadata(self, packet):
    wid = packet[1]
    metadata = packet[2]
    
    window = self.windows.get(wid)
    if not window:
        return
    
    # Update window properties
    if "title" in metadata:
        window.set_title(metadata["title"])
    
    if "icon" in metadata:
        icon = self.decode_icon(metadata["icon"])
        window.set_icon(icon)
    
    if "size-constraints" in metadata:
        sc = metadata["size-constraints"]
        if "minimum-size" in sc:
            window.set_minimum_size(*sc["minimum-size"])
        if "maximum-size" in sc:
            window.set_maximum_size(*sc["maximum-size"])
    
    if "maximized" in metadata:
        if metadata["maximized"]:
            window.showMaximized()
        else:
            window.showNormal()
```

## Window Decorations

### Server-side Decorations (SSD)

Server draws decorations, sends as part of window content:

```python
metadata["decorations"] = True
# Client creates borderless window
# Decorations are part of pixel content
```

### Client-side Decorations (CSD)

Native OS draws decorations:

```python
metadata["decorations"] = False
# Client lets OS add title bar/borders
```

### Frame Extents

Space occupied by decorations:

```python
# Server → Client
["window-metadata", wid, {
    "frame-extents": (left, right, top, bottom)
}]

# Example: Standard title bar + border
"frame-extents": (1, 1, 30, 1)
#                 L  R  T   B
```

## Window Stacking Order

### Z-Order Management

```python
# Keep windows in correct stacking order
class XpraClient:
    def __init__(self):
        self.window_stack = []  # Bottom to top
    
    def _process_raise_window(self, packet):
        wid = packet[1]
        
        # Move to top of stack
        if wid in self.window_stack:
            self.window_stack.remove(wid)
        self.window_stack.append(wid)
        
        # Raise native window
        window = self.windows[wid]
        window.raise_()
    
    def _process_restack(self, packet):
        """Update complete z-order"""
        new_stack = packet[1]  # [wid1, wid2, ...]
        self.window_stack = new_stack
        
        # Apply to native windows
        for i, wid in enumerate(new_stack):
            window = self.windows[wid]
            window.set_z_order(i)
```

## Multi-Monitor Support

### Monitor Configuration

```python
# Client → Server: Screen configuration
["desktop_size", total_width, total_height, 
 max_width, max_height, screen_sizes]

# Example: 2 monitors
["desktop_size", 3840, 1080, 3840, 1080, [
    (0, 0, 1920, 1080, 527, 296, 0, 0, "HDMI-1"),  # Left monitor
    (1920, 0, 1920, 1080, 527, 296, 0, 0, "DP-1"),  # Right monitor
]]
```

### Window Placement on Monitors

```python
# Client tells server which monitor window is on
["map-window", wid, x, y, width, height, {
    "screen": 1,  # Monitor index
}]

# Server remembers and uses for new windows
def place_new_window(self, window):
    # Try to open on same monitor as parent
    # Or on monitor where mouse is
    # Or on primary monitor
```

## Window Groups

### Application Window Groups

```python
# Windows from same application
metadata["group-leader"] = main_window_xid

# Client can:
# - Minimize/restore group together
# - Show grouped in taskbar
# - Keep related windows together
```

## Special Window Behaviors

### Always on Top

```python
metadata["above"] = True

# Client implementation
window.setWindowFlag(Qt.WindowStaysOnTopHint)
```

### Skip Taskbar

```python
metadata["skip-taskbar"] = True

# Don't show in taskbar/dock
window.setWindowFlag(Qt.Tool)
```

### Sticky (All Workspaces)

```python
metadata["sticky"] = True

# Show on all virtual desktops
window.make_sticky()
```

## Window Icons

### Icon Encoding

```python
# Server encodes icon as PNG
icon_png = encode_png(icon_rgba_data, width, height)

metadata["icon"] = icon_png
metadata["icon-size"] = (64, 64)

# Multiple sizes
metadata["icons"] = {
    "16x16": icon_16_png,
    "32x32": icon_32_png,
    "64x64": icon_64_png,
}
```

### Client Icon Handling

```python
def set_window_icon(self, window, icon_data):
    # Decode PNG
    pixbuf = decode_png(icon_data)
    
    # Set as window icon
    window.set_icon(pixbuf)  # GTK
    # or
    icon = QIcon(QPixmap.fromImage(qimage))
    window.setWindowIcon(icon)  # Qt
```

---

**Next:** [Rendering và Drawing](05-rendering.md)

