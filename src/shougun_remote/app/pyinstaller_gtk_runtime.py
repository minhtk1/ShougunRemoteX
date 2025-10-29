"""
PyInstaller runtime hook để setup GTK3 runtime paths.
Code copied from xpra-client under GNU General Public License v2.0
"""
import os
import sys

# Lấy đường dẫn đến thư mục temp của PyInstaller (nơi extract các file)
if getattr(sys, 'frozen', False):
    # PyInstaller tạo biến _MEIPASS chứa đường dẫn đến temp directory
    base_path = sys._MEIPASS
else:
    # Chạy từ source code
    base_path = os.path.dirname(os.path.abspath(__file__))

# Thiết lập PATH để tìm DLL trong thư mục lib
lib_path = os.path.join(base_path, "lib")
if os.path.exists(lib_path):
    # Thêm lib path vào PATH để Windows tìm thấy DLL
    path = os.environ.get("PATH", "")
    if lib_path not in path:
        os.environ["PATH"] = f"{lib_path}{os.path.pathsep}{path}"

# Thiết lập GI_TYPELIB_PATH cho gi.repository
girepo_path = os.path.join(base_path, "lib", "girepository-1.0")
if os.path.exists(girepo_path):
    os.environ["GI_TYPELIB_PATH"] = girepo_path

# Thiết lập các biến môi trường khác cho GTK3
gtk_lib_path = os.path.join(base_path, "lib")
if os.path.exists(gtk_lib_path):
    # GDK_PIXBUF_MODULE_FILE - đường dẫn đến cache file của gdk-pixbuf loaders
    gdk_pixbuf_dir = os.path.join(gtk_lib_path, "gdk-pixbuf-2.0")
    if os.path.exists(gdk_pixbuf_dir):
        # Tìm thư mục loaders (thường là 2.10.0)
        for item in os.listdir(gdk_pixbuf_dir):
            loaders_path = os.path.join(gdk_pixbuf_dir, item, "loaders")
            if os.path.isdir(loaders_path):
                cache_file = os.path.join(loaders_path, "loaders.cache")
                if os.path.exists(cache_file):
                    os.environ["GDK_PIXBUF_MODULEDIR"] = loaders_path
                    os.environ["GDK_PIXBUF_MODULE_FILE"] = cache_file
                    break
    
    # GIO_MODULE_DIR cho gio modules
    gio_modules_dir = os.path.join(gtk_lib_path, "gio", "modules")
    if os.path.exists(gio_modules_dir):
        os.environ["GIO_MODULE_DIR"] = gio_modules_dir

# FONTCONFIG_FILE - đường dẫn đến fontconfig config
etc_path = os.path.join(base_path, "etc")
if os.path.exists(etc_path):
    fontconfig_conf = os.path.join(etc_path, "fonts", "fonts.conf")
    if os.path.exists(fontconfig_conf):
        os.environ["FONTCONFIG_FILE"] = fontconfig_conf

