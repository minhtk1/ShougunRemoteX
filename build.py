"""
Unified build script for:
 - ShougunRemoteX_Service.exe (existing)
 - Xpra_cmd.exe (new)
"""

import os
import sys
import PyInstaller.__main__
import platform


def parse_args() -> str:
    config = "Release"
    for i, arg in enumerate(sys.argv):
        if arg == "-Config" and i + 1 < len(sys.argv):
            config = sys.argv[i + 1]
            break
    return config


def build(config: str) -> None:
    output_dir = os.path.join("dist", config)
    os.makedirs(output_dir, exist_ok=True)
    
    # Xác định dấu phân cách cho --add-data dựa trên hệ điều hành
    # Windows sử dụng dấu ;, Linux/macOS sử dụng dấu :
    data_separator = ";" if platform.system() == "Windows" else ":"
    
    # Xác định extension cho executable dựa trên hệ điều hành
    exe_extension = ".exe" if platform.system() == "Windows" else ""

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
            "--hidden-import",
            "pywin32",
            "--hidden-import",
            "pythonnet",
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
            "python_service.py",
        ]
    )

    # 2) Build Xpra_cmd.exe
    print("Building Xpra_cmd.exe...")
    PyInstaller.__main__.run(
        [
            *base_options,
            "--name",
            f"Xpra_cmd{exe_extension}",
            "--hidden-import",
            "shougun_remote",
            "--hidden-import",
            "third_party.xpra_client",
            "--hidden-import",
            "xpra.common",
            "--hidden-import",
            "xpra.scripts.main",
            "--hidden-import",
            "xpra.util.env",
            "--hidden-import",
            "rencode",
            "--collect-all",
            "gi",
            "--collect-all",
            "cairo",
            "--collect-all",
            "PIL",
            os.path.join("src", "shougun_remote", "app", "cli_xpra.py"),
        ]
    )

    print("\n✅ Build completed:")
    print(f"   {os.path.join(output_dir, f'ShougunRemoteX_Service{exe_extension}')}")
    print(f"   {os.path.join(output_dir, f'Xpra_cmd{exe_extension}')}")


if __name__ == "__main__":
    cfg = parse_args()
    build(cfg)
