# This file is part of Xpra.
# Copyright (C) 2011 Antoine Martin <antoine@xpra.org>
# Xpra is released under the terms of the GNU GPL v2, or, at your option, any
# later version. See the file COPYING for details.

from __future__ import annotations

from xpra.os_util import OSX, POSIX, gi_import
from xpra.util.env import first_time, IgnoreWarningsContext
from xpra.util.system import is_X11
from xpra.log import Logger

Gdk = gi_import("Gdk")

# Kiểm tra và định nghĩa Gdk.GrabStatus proxy một cách an toàn
# Trên Windows với GTK3, Gdk.GrabStatus có thể không tồn tại hoặc có cách truy cập khác
# Tạo một proxy object để thay thế Gdk.GrabStatus khi nó không tồn tại
if not hasattr(Gdk, 'GrabStatus'):
    # Fallback: tạo một object giả với các thuộc tính cần thiết
    class FallbackGrabStatus:
        """Fallback object cho Gdk.GrabStatus khi không tồn tại trên platform"""
        SUCCESS = 0
        ALREADY_GRABBED = 1
        INVALID_TIME = 2
        NOT_VIEWABLE = 3
        FROZEN = 4
        FAILED = 5  # Không có trong GRAB_STATUS_STRING nhưng được sử dụng trong code
    
    # Gán vào Gdk để có thể sử dụng Gdk.GrabStatus trong code khác
    # Lưu ý: gi_import trả về cùng một singleton, vì vậy việc gán này sẽ có tác dụng
    # với tất cả các module khác nếu util.py được import trước
    try:
        Gdk.GrabStatus = FallbackGrabStatus
    except (TypeError, AttributeError):
        # Nếu không thể gán trực tiếp, tạo một wrapper
        pass

# Định nghĩa GRAB_STATUS_STRING với các giá trị từ Gdk.GrabStatus
# Sử dụng try-except để xử lý trường hợp Gdk.GrabStatus không tồn tại
try:
    # Thử truy cập Gdk.GrabStatus
    if hasattr(Gdk, 'GrabStatus'):
        GRAB_STATUS_STRING = {
            Gdk.GrabStatus.SUCCESS: "SUCCESS",
            Gdk.GrabStatus.ALREADY_GRABBED: "ALREADY_GRABBED",
            Gdk.GrabStatus.INVALID_TIME: "INVALID_TIME",
            Gdk.GrabStatus.NOT_VIEWABLE: "NOT_VIEWABLE",
            Gdk.GrabStatus.FROZEN: "FROZEN",
        }
        # Thêm FAILED nếu có
        if hasattr(Gdk.GrabStatus, 'FAILED'):
            GRAB_STATUS_STRING[Gdk.GrabStatus.FAILED] = "FAILED"
    else:
        # Fallback: sử dụng các giá trị số nếu enum không tồn tại
        GRAB_STATUS_STRING = {
            0: "SUCCESS",
            1: "ALREADY_GRABBED",
            2: "INVALID_TIME",
            3: "NOT_VIEWABLE",
            4: "FROZEN",
            5: "FAILED",
        }
except (AttributeError, TypeError) as e:
    # Nếu không thể truy cập Gdk.GrabStatus, sử dụng giá trị fallback
    log = Logger("gtk", "util")
    log.warn(f"Warning: Cannot access Gdk.GrabStatus: {e}")
    log.warn("Using fallback GRAB_STATUS_STRING values")
    GRAB_STATUS_STRING = {
        0: "SUCCESS",
        1: "ALREADY_GRABBED",
        2: "INVALID_TIME",
        3: "NOT_VIEWABLE",
        4: "FROZEN",
        5: "FAILED",
    }


def get_default_root_window() -> Gdk.Window | None:
    screen = Gdk.Screen.get_default()
    if screen is None:
        return None
    return screen.get_root_window()


def get_root_size(default: None | tuple[int, int] = (1920, 1024)) -> tuple[int, int] | None:
    if OSX:
        # the easy way:
        root = get_default_root_window()
        if not root:
            return default
        w, h = root.get_geometry()[2:4]
    else:
        # GTK3 on win32 triggers this warning:
        # "GetClientRect failed: Invalid window handle."
        # if we try to use the root window,
        # and on Linux with Wayland, we get bogus values...
        screen = Gdk.Screen.get_default()
        if screen is None:
            return default
        with IgnoreWarningsContext():
            w = screen.get_width()
            h = screen.get_height()
    if w <= 0 or h <= 0 or w > 32768 or h > 32768:
        if first_time("Gtk root window dimensions"):
            log = Logger("gtk", "screen")
            log.warn(f"Warning: Gdk returned invalid root window dimensions: {w}x{h}")
            log.warn(" no access to the display?")
            log.warn(f" using {default} instead")
        return default
    return w, h

dsinit: bool = False


def init_display_source() -> None:
    """
    On X11, we want to be able to access the bindings,
    so we need to get the X11 display from GDK.
    """
    global dsinit
    dsinit = True
    x11 = is_X11()
    log = Logger("gtk", "screen")
    log(f"init_display_source() {x11=}")
    if x11:
        try:
            from xpra.x11.gtk.display_source import init_gdk_display_source
            init_gdk_display_source()
        except ImportError:  # pragma: no cover
            log("init_gdk_display_source()", exc_info=True)
            log.warn("Warning: the Gtk-3.0 X11 bindings are missing")
            log.warn(" some features may be degraded or unavailable")
            log.warn(" ie: keyboard mapping, focus, etc")


def ds_inited() -> bool:
    return dsinit


def main():
    from xpra.platform import program_context
    from xpra.util.str_fn import print_nested_dict
    from xpra.log import enable_color
    with program_context("GTK-Version-Info", "GTK Version Info"):
        enable_color()
        from xpra.gtk.versions import get_gtk_version_info
        print("%s" % get_gtk_version_info())
        if POSIX and not OSX:
            from xpra.x11.bindings.posix_display_source import init_posix_display_source
            init_posix_display_source()
        import warnings
        warnings.simplefilter("ignore")
        from xpra.gtk.info import get_display_info, get_screen_sizes
        print(get_screen_sizes()[0])
        print_nested_dict(get_display_info())


if __name__ == "__main__":
    main()
