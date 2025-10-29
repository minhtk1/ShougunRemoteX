"""
Unified build script for:
 - ShougunRemoteX_Service.exe (existing)
 - Xpra_cmd.exe (new)
"""

import os
import sys
import PyInstaller.__main__


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
            "ShougunRemoteX_Service",
            "--add-data",
            "src;src",
            "--add-data",
            "config;config",
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
            "Xpra_cmd",
            "--hidden-import",
            "shougun_remote",
            "--hidden-import",
            "third_party.xpra_client",
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
    print(f"   {os.path.join(output_dir, 'ShougunRemoteX_Service.exe')}")
    print(f"   {os.path.join(output_dir, 'Xpra_cmd.exe')}")


if __name__ == "__main__":
    cfg = parse_args()
    build(cfg)
