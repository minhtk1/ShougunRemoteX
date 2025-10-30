"""
Unified build script for:
 - ShougunRemoteX_Service.exe (existing)
 - Xpra_cmd.exe (new)
"""

import os
import sys
import PyInstaller.__main__
import platform
import subprocess


def parse_args() -> str:
    config = "Release"
    for i, arg in enumerate(sys.argv):
        if arg == "-Config" and i + 1 < len(sys.argv):
            config = sys.argv[i + 1]
            break
    return config


def install_gtk_packages() -> None:
    """Cài đặt PyGObject và PyCairo từ GTK3 runtime"""
    gtk_root = os.path.abspath(os.path.join("libs", "GTK3_Gvsbuild_2024.11.0_x64"))
    python_dir = os.path.join(gtk_root, "python")
    
    if not os.path.exists(python_dir):
        print("Warning: GTK3 python directory not found, skipping PyGObject installation")
        return
    
    # Tìm các file wheel
    wheel_files = []
    for file in os.listdir(python_dir):
        if file.endswith('.whl'):
            wheel_files.append(os.path.join(python_dir, file))
    
    if not wheel_files:
        print("Warning: No wheel files found in GTK3 python directory")
        return
    
    print("Installing PyGObject and PyCairo from GTK3 runtime...")
    for wheel_file in wheel_files:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", wheel_file, "--force-reinstall"], 
                         check=True, capture_output=True)
            print(f"  Installed: {os.path.basename(wheel_file)}")
        except subprocess.CalledProcessError as e:
            print(f"  Warning: Failed to install {os.path.basename(wheel_file)}: {e}")
            print(f"  stderr: {e.stderr.decode() if e.stderr else 'No error details'}")


def setup_gtk_environment() -> None:
    """Thiết lập environment variables cho GTK3 runtime để PyInstaller có thể tìm thấy DLLs"""
    gtk_root = os.path.abspath(os.path.join("libs", "GTK3_Gvsbuild_2024.11.0_x64"))
    gtk_bin = os.path.join(gtk_root, "bin")
    gtk_lib = os.path.join(gtk_root, "lib")
    
    if not os.path.exists(gtk_bin):
        print("Warning: GTK3 bin directory not found, skipping environment setup")
        return
    
    print("Setting up GTK3 environment variables...")
    
    # Thêm GTK3 bin directory vào PATH
    current_path = os.environ.get("PATH", "")
    if gtk_bin not in current_path:
        os.environ["PATH"] = f"{gtk_bin};{current_path}"
        print(f"  Added {gtk_bin} to PATH")
    
    # Thiết lập các environment variables cần thiết cho GTK3
    os.environ["GTK_PATH"] = gtk_root
    os.environ["GI_TYPELIB_PATH"] = os.path.join(gtk_lib, "girepository-1.0")
    os.environ["GDK_PIXBUF_MODULE_FILE"] = os.path.join(gtk_lib, "gdk-pixbuf-2.0", "2.10.0", "loaders.cache")
    os.environ["FONTCONFIG_PATH"] = os.path.join(gtk_root, "etc", "fonts")
    os.environ["FONTCONFIG_FILE"] = os.path.join(gtk_root, "etc", "fonts", "fonts.conf")
    
    # Thiết lập PKG_CONFIG_PATH để tìm thấy .pc files
    pkg_config_path = os.path.join(gtk_lib, "pkgconfig")
    if os.path.exists(pkg_config_path):
        os.environ["PKG_CONFIG_PATH"] = pkg_config_path
    
    print("  Environment variables set successfully")


def build(config: str) -> None:
    output_dir = os.path.join("dist", config)
    os.makedirs(output_dir, exist_ok=True)
    
    # Cài đặt PyGObject và PyCairo từ GTK3 runtime
    install_gtk_packages()
    
    # Thiết lập environment variables cho GTK3 runtime
    setup_gtk_environment()
    
    # Xác định dấu phân cách cho --add-data dựa trên hệ điều hành
    # Windows sử dụng dấu ;, Linux/macOS sử dụng dấu :
    data_separator = ";" if platform.system() == "Windows" else ":"
    
    # Xác định extension cho executable dựa trên hệ điều hành
    exe_extension = ".exe" if platform.system() == "Windows" else ""
    
    # GTK3 runtime từ gvsbuild - cần thiết cho Xpra_cmd.exe
    gtk_root = os.path.abspath(os.path.join("libs", "GTK3_Gvsbuild_2024.11.0_x64"))
    gtk_bin = os.path.join(gtk_root, "bin")
    gtk_lib = os.path.join(gtk_root, "lib")
    gtk_girepo = os.path.join(gtk_lib, "girepository-1.0")
    gtk_etc = os.path.join(gtk_root, "etc")
    gtk_site_packages = os.path.join(gtk_lib, "site-packages")

    base_options = [
        "--onefile",
        "--distpath",
        output_dir,
        "--workpath",
        os.path.join("build", config),
        "--specpath",
        "build",
        "--paths",
        "src",
        "--paths",
        ".",
        "--clean",  # Thêm option để clean build cache
    ]
    
    # Thêm đường dẫn đến GTK3 site-packages để PyInstaller có thể tìm thấy PyGObject
    if os.path.exists(gtk_site_packages):
        base_options.extend([
            "--paths",
            gtk_site_packages,
        ])

    if config == "Debug":
        base_options.extend(["--console", "--debug", "all"])
    else:
        base_options.append("--noconsole")

    print(f"Building {config} configuration...")

    # 1) Build ShougunRemoteX_Service.exe
    print("Building ShougunRemoteX_Service.exe...")
    PyInstaller.__main__.run(
        [
            *base_options,
            "--name",
            f"ShougunRemoteX_Service{exe_extension}",
            "--add-data",
            f"{os.path.abspath('config')}{data_separator}config",
            "--hidden-import",
            "psutil",
            # "--hidden-import",
            # "pywin32",  # PyInstaller tự động detect pywin32
            "--hidden-import",
            "pydantic",
            "--hidden-import",
            "loguru",
            "--hidden-import",
            "yaml",
            "--hidden-import",
            "shougun_remote",
            "--hidden-import",
            "shougun_remote.services",
            "--hidden-import",
            "shougun_remote.core",
            "--hidden-import",
            "shougun_remote.config",
            "--hidden-import",
            "shougun_remote.models",
            "--hidden-import",
            "shougun_remote.repositories",
            "--hidden-import",
            "shougun_remote.monitors",
            "--hidden-import",
            "watchdog",
            "--hidden-import",
            "watchdog.observers",
            "--hidden-import",
            "watchdog.events",
            "--hidden-import",
            "importlib_resources",
            # Không còn dùng trees API của importlib_resources
            "python_service.py",
        ]
    )

    # 2) Build Xpra_cmd.exe với GTK3 runtime
    print("Building Xpra_cmd.exe...")
    
    # Chuẩn bị các file GTK3 cần thiết
    gtk_options = []
    # Không sử dụng đường dẫn ngoài dự án cho xpra; chỉ bundle những gì nằm trong dự án
    # hoặc được cài trong môi trường ảo để đảm bảo tính tự chứa của sản phẩm build
    if os.path.exists(gtk_bin):
        # Copy tất cả DLL từ GTK3 bin directory
        print(f"  Including GTK3 DLLs from {gtk_bin}...")
        dll_files = [f for f in os.listdir(gtk_bin) if f.endswith('.dll')]
        for dll_file in dll_files:
            src_path = os.path.join(gtk_bin, dll_file)
            gtk_options.extend([
                "--add-binary",
                f"{src_path}{data_separator}lib",  # Copy vào thư mục lib trong temp
            ])
    
    if os.path.exists(gtk_girepo):
        # Copy typelib files cho gi.repository
        print(f"  Including GTK3 typelib files from {gtk_girepo}...")
        gtk_options.extend([
            "--add-data",
            f"{gtk_girepo}{data_separator}lib/girepository-1.0",
        ])
    
    # Copy gdk-pixbuf loaders
    gdk_pixbuf_loaders = os.path.join(gtk_lib, "gdk-pixbuf-2.0")
    if os.path.exists(gdk_pixbuf_loaders):
        print(f"  Including gdk-pixbuf loaders from {gdk_pixbuf_loaders}...")
        gtk_options.extend([
            "--add-data",
            f"{gdk_pixbuf_loaders}{data_separator}lib/gdk-pixbuf-2.0",
        ])
    
    # Copy gio modules
    gio_modules = os.path.join(gtk_lib, "gio", "modules")
    if os.path.exists(gio_modules):
        print(f"  Including gio modules from {gio_modules}...")
        gtk_options.extend([
            "--add-data",
            f"{gio_modules}{data_separator}lib/gio/modules",
        ])
    
    # Copy config files (etc directory) - cần thiết cho fontconfig, SSL, etc.
    if os.path.exists(gtk_etc):
        print(f"  Including GTK3 config files from {gtk_etc}...")
        gtk_options.extend([
            "--add-data",
            f"{gtk_etc}{data_separator}etc",
        ])
    
    # Copy PyGObject và PyCairo từ GTK3 site-packages
    if os.path.exists(gtk_site_packages):
        print(f"  Including PyGObject and PyCairo from {gtk_site_packages}...")
        gtk_options.extend([
            "--add-data",
            f"{gtk_site_packages}{data_separator}lib/site-packages",
        ])
        
        # Thêm các file Python cụ thể để đảm bảo PyInstaller tìm thấy chúng
        gi_path = os.path.join(gtk_site_packages, "gi")
        cairo_path = os.path.join(gtk_site_packages, "cairo")
        if os.path.exists(gi_path):
            gtk_options.extend([
                "--add-data",
                f"{gi_path}{data_separator}lib/site-packages/gi",
            ])
        if os.path.exists(cairo_path):
            gtk_options.extend([
                "--add-data",
                f"{cairo_path}{data_separator}lib/site-packages/cairo",
            ])
    
    PyInstaller.__main__.run(
        [
            *base_options,
            *gtk_options,
            "--name",
            f"Xpra_cmd{exe_extension}",
            "--additional-hooks-dir",
            os.path.join("src", "shougun_remote", "app"),
            "--hidden-import",
            "shougun_remote",
            "--hidden-import",
            "shougun_remote.app.pyinstaller_gtk_runtime",
            "--hidden-import",
            "xpra.util.pysystem",
            # Xpra client modules - cần thiết cho xpra.client.gtk3.client import
            "--hidden-import",
            "xpra",
            "--hidden-import",
            "xpra.client",
            "--hidden-import",
            "xpra.client.gtk3",
            "--hidden-import",
            "xpra.client.gtk3.client",
            "--hidden-import",
            "xpra.client.gtk3.client_base",
            "--hidden-import",
            "xpra.client.gtk3.window",
            "--hidden-import",
            "xpra.client.gtk3.window_base",
            "--hidden-import",
            "xpra.client.gtk3.keyboard_helper",
            "--hidden-import",
            "xpra.client.gtk3.cairo_backing",
            "--hidden-import",
            "xpra.client.base",
            "--hidden-import",
            "xpra.client.base.client",
            "--hidden-import",
            "xpra.client.gui",
            "--hidden-import",
            "xpra.client.mixins",
            "--hidden-import",
            "xpra.os_util",
            "--hidden-import",
            "xpra.util",
            "--hidden-import",
            "xpra.util.system",
            "--hidden-import",
            "xpra.platform",
            "--hidden-import",
            "xpra.platform.gui",
            "--hidden-import",
            "xpra.log",
            "--hidden-import",
            "xpra.common",
            "--hidden-import",
            "xpra.net",
            "--hidden-import",
            "xpra.gtk",
            "--hidden-import",
            "xpra.clipboard",
            "--hidden-import",
            "xpra.codecs",
            "--hidden-import",
            "xpra.keyboard",
            "--hidden-import",
            "xpra.gtk",
            "--hidden-import",
            "xpra.gtk.gobject",
            "--hidden-import",
            "xpra.gtk.util",
            "--hidden-import",
            "xpra.gtk.window",
            "--hidden-import",
            "xpra.gtk.pixbuf",
            "--hidden-import",
            "xpra.gtk.keymap",
            "--hidden-import",
            "xpra.gtk.cursors",
            "--hidden-import",
            "xpra.gtk.info",
            "--hidden-import",
            "xpra.gtk.widget",
            "--hidden-import",
            "xpra.gtk.versions",
            "--hidden-import",
            "xpra.gtk.css_overrides",
            "--hidden-import",
            "xpra.gtk.cairo_image",
            "--hidden-import",
            "xpra.gtk.notifier",
            "--hidden-import",
            "xpra.client.gtk3.notifier",
            "--hidden-import",
            "xpra.notifications",
            "--hidden-import",
            "xpra.notifications.notifier_base",
            "--hidden-import",
            "xpra.client.gui",
            "--hidden-import",
            "xpra.client.gui.window_base",
            "--hidden-import",
            "xpra.client.gui.keyboard_helper",
            "--hidden-import",
            "xpra.client.gui.ui_client_base",
            "--hidden-import",
            "xpra.scripts",
            "--hidden-import",
            "xpra.scripts.config",
            "--hidden-import",
            "xpra.net.common",
            "--hidden-import",
            "xpra.net.crypto",
            "--hidden-import",
            "xpra.net.digest",
            # Bổ sung module cần thiết cho tính năng in file qua mạng của xpra
            # Tránh lỗi: ModuleNotFoundError: No module named 'xpra.net.file_transfer'
            "--hidden-import",
            "xpra.net.file_transfer",
            # Thu thập toàn bộ submodules trong xpra.net (đảm bảo không thiếu module phụ)
            "--collect-submodules",
            "xpra.net",
            "--collect-submodules",
            "xpra.client",
            "--collect-submodules",
            "xpra.client.gtk3",
            "--collect-submodules",
            "xpra.client.gui",
            "--collect-submodules",
            "xpra.client.mixins",
            "--collect-submodules",
            "xpra.platform",
            "--collect-submodules",
            "xpra.os_util",
            "--collect-submodules",
            "xpra.util",
            "--collect-submodules",
            "xpra.gtk",
            "--collect-data",
            "xpra",
            "--collect-data",
            "xpra.client",
            "--hidden-import",
            "xpra.client.gui.window_border",
            "--hidden-import",
            "xpra.client.mixins.windows",
            "--hidden-import",
            "xpra.codecs.constants",
            "--hidden-import",
            "xpra.client.gui.keyboard_shortcuts_parser",
            "--hidden-import",
            "xpra.util.stats",
            "--hidden-import",
            "xpra.util.objects",
            "--hidden-import",
            "xpra.util.str_fn",
            "--hidden-import",
            "xpra.util.env",
            "--hidden-import",
            "xpra.util.child_reaper",
            "--hidden-import",
            "xpra.util.io",
            "--hidden-import",
            "xpra.keyboard.common",
            "--hidden-import",
            "xpra.exit_codes",
            "--hidden-import",
            "importlib_resources",
            # Không còn dùng trees API của importlib_resources
            # PyGObject (gi module) - cần thiết cho GTK3 backend
            "--hidden-import",
            "gi",
            "--hidden-import",
            "gi.repository",
            "--hidden-import",
            "gi.repository.Gtk",
            "--hidden-import",
            "gi.repository.Gdk",
            "--hidden-import",
            "gi.repository.GObject",
            "--hidden-import",
            "gi.repository.GLib",
            "--hidden-import",
            "gi.repository.Gio",
            "--hidden-import",
            "gi.repository.Pango",
            "--hidden-import",
            "gi.repository.PangoCairo",
            "--hidden-import",
            "gi.repository.GdkPixbuf",
            "--hidden-import",
            "gi.repository.cairo",
            "--hidden-import",
            "gi.overrides",
            "--hidden-import",
            "gi.overrides.Gtk",
            "--hidden-import",
            "gi.overrides.Gdk",
            # Chỉ collect các gi.repository modules cần thiết, KHÔNG dùng --collect-all gi
            # để tránh warnings về GStreamer typelib files không tìm thấy
            # (GStreamer không được cài đặt trong GTK3 runtime từ gvsbuild)
            "--collect-all",
            "cairo",
            "--collect-all",
            "PIL",
            os.path.join("src", "shougun_remote", "app", "cli_xpra.py"),
        ]
    )

    print("\nBuild completed:")
    print(f"   {os.path.join(output_dir, f'ShougunRemoteX_Service{exe_extension}')}")
    print(f"   {os.path.join(output_dir, f'Xpra_cmd{exe_extension}')}")


if __name__ == "__main__":
    cfg = parse_args()
    build(cfg)
