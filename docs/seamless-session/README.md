# Xpra Seamless Session - Tài liệu Kỹ thuật Đầy đủ

## 📚 Mục lục

1. [Tổng quan](#tổng-quan)
2. [Kiến trúc hệ thống](01-architecture.md)
3. [Chi tiết Protocol](02-protocol.md)
4. [Quy trình kết nối](03-connection.md)
5. [Quản lý Windows](04-window-management.md)
6. [Rendering và Drawing](05-rendering.md)
7. [Hướng dẫn Implementation](06-implementation.md)
8. [Code Examples](07-code-examples.md)

---

## Tổng quan

### Seamless Session là gì?

**Seamless Session** là chế độ hoạt động chính của Xpra, cho phép forward các cửa sổ ứng dụng từ X11 server đến client một cách **riêng lẻ**, không bị gói trong một desktop window như VNC.

### Điểm khác biệt chính

```
┌─────────────────────────────────────────────────────────┐
│                    Desktop của Client                    │
│                                                          │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │ Local App 1  │     │ Remote App A │ ← Seamless!     │
│  └──────────────┘     └──────────────┘                 │
│                                                          │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │ Local App 2  │     │ Remote App B │ ← Seamless!     │
│  └──────────────┘     └──────────────┘                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Người dùng không phân biệt được** đâu là app local, đâu là app remote!

### So sánh với các mode khác

| Feature | Seamless Mode | Desktop Mode | Shadow Mode |
|---------|---------------|--------------|-------------|
| Window forwarding | ✅ Từng window riêng | ❌ Toàn bộ desktop | ✅ Clone display |
| Window management latency | ⚡ Cực thấp (client-side) | 🐌 Cao (network) | 🐌 Cao (network) |
| Hoạt động như local app | ✅ Hoàn toàn | ❌ Không | ❌ Không |
| Yêu cầu X11 server | ✅ Có | ✅ Có | ⚠️ Không (clone existing) |
| Hỗ trợ Windows/macOS server | ❌ Không | ❌ Không | ✅ Có |

### Ưu điểm vượt trội

1. **Zero latency window management**: Move, resize, minimize được xử lý local
2. **Native integration**: Windows xuất hiện trong taskbar, Alt+Tab như app thật
3. **Persistence**: Disconnect/reconnect không mất state
4. **Better UX**: Không bị giới hạn trong canvas như VNC
5. **Feature-rich**: Audio, clipboard, printing, notifications... tất cả được sync

### Kiến trúc tổng quan

```
┌───────────────────────────────────────────────────────────────┐
│                         SERVER (Linux/X11)                     │
│                                                                │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│  │ xterm    │   │ firefox  │   │ gimp     │                  │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                  │
│       └──────────────┴──────────────┘                         │
│                      │                                         │
│              ┌───────▼────────┐                               │
│              │  X11 Display   │                               │
│              │   :100         │                               │
│              └───────┬────────┘                               │
│                      │                                         │
│              ┌───────▼────────┐                               │
│              │  Xpra Server   │                               │
│              │  - Detect new windows                          │
│              │  - Capture pixels                              │
│              │  - Encode data                                 │
│              └───────┬────────┘                               │
└──────────────────────┼────────────────────────────────────────┘
                       │
                 Network Protocol
           (SSH/TCP/WebSocket/SSL/QUIC)
                       │
┌──────────────────────▼────────────────────────────────────────┐
│                    CLIENT (Any OS)                            │
│                                                                │
│              ┌────────────────┐                               │
│              │  Xpra Client   │                               │
│              │  - Receive packets                             │
│              │  - Decode data                                 │
│              │  - Create windows                              │
│              └────────┬───────┘                               │
│                       │                                        │
│       ┌───────────────┼───────────────┐                       │
│       │               │               │                       │
│  ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐                 │
│  │ Window 1 │   │ Window 2 │   │ Window 3 │                 │
│  │ (xterm)  │   │(firefox) │   │  (gimp)  │                 │
│  └──────────┘   └──────────┘   └──────────┘                 │
│       ↑               ↑               ↑                        │
│       └───────────────┴───────────────┘                       │
│              Native OS Window Manager                          │
│           (Windows DWM / macOS Quartz / X11)                  │
└───────────────────────────────────────────────────────────────┘
```

### Use cases chính

1. **Remote Development**: Code trên server, hiển thị IDE local
2. **High-performance Computing**: Chạy app nặng trên server, điều khiển từ laptop
3. **Multi-location Access**: Làm việc từ nhiều nơi, cùng session
4. **Secure Environment**: App chạy trong isolated server, chỉ hiển thị output
5. **Legacy Applications**: Chạy app cũ cần X11, hiển thị trên Windows/macOS

### Yêu cầu hệ thống

**Server:**
- ✅ Linux với X11 (hoặc Xvfb/Xdummy)
- ✅ Xpra server package
- ✅ Applications cần forward

**Client:**
- ✅ Xpra client cho OS tương ứng (Windows/macOS/Linux)
- ✅ Hoặc HTML5 browser
- ✅ Network connection đến server

---

## Quick Start

### Cách sử dụng cơ bản

```bash
# 1. Start seamless session với xterm
xpra start ssh://user@server/ --start-child=xterm

# 2. Start nhiều apps
xpra start ssh://user@server/ \
  --start-child=xterm \
  --start-child=firefox \
  --start-child=gedit

# 3. Attach vào session đang chạy
xpra attach ssh://user@server/100

# 4. List sessions
xpra list

# 5. Detach (Ctrl+C hoặc đóng client window)

# 6. Stop session
xpra stop ssh://user@server/100
```

### Session persistence

```bash
# Day 1: Start session
xpra start :100 --start=firefox
xpra attach :100
# ... work work work ...
# Disconnect (Ctrl+C)

# Day 2: Reconnect
xpra attach :100
# Firefox vẫn đang chạy, tất cả tabs vẫn còn!
```

---

## Tài liệu chi tiết

Để hiểu sâu về cách implement Seamless Session, vui lòng đọc các tài liệu sau theo thứ tự:

1. **[Kiến trúc hệ thống](01-architecture.md)** - Hiểu cấu trúc tổng thể
2. **[Chi tiết Protocol](02-protocol.md)** - Format packets, encoding
3. **[Quy trình kết nối](03-connection.md)** - Từ connect đến authenticated
4. **[Quản lý Windows](04-window-management.md)** - Create, update, destroy windows
5. **[Rendering và Drawing](05-rendering.md)** - Decode và vẽ pixels
6. **[Hướng dẫn Implementation](06-implementation.md)** - Build client từ đầu
7. **[Code Examples](07-code-examples.md)** - Ví dụ code thực tế

---

## Glossary

- **WID**: Window ID - Unique identifier cho mỗi window
- **Packet**: Đơn vị dữ liệu trong protocol
- **Encoding**: Cách encode pixel data (rgb, png, jpeg, h264, vp9...)
- **Damage**: Vùng màn hình cần update
- **Override-redirect**: Window loại đặc biệt (menus, tooltips) không có decorations
- **Metadata**: Thông tin về window (title, icon, size hints...)
- **Rencodeplus**: Custom encoding format của Xpra
- **MMAP**: Shared memory transfer (nhanh hơn network)

---

## Tham khảo

- [Xpra Official Documentation](../../docs/README.md)
- [Xpra GitHub Repository](https://github.com/Xpra-org/xpra)
- [Xpra Protocol Specification](../../docs/Network/Protocol.md)
- [X11 Protocol](https://www.x.org/releases/current/doc/)

---

**Created by:** minhtk  
**Last updated:** 2025-10-28  
**Version:** 1.0

