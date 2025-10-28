# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['python_service.py'],
    pathex=['src', '.'],
    binaries=[],
    datas=[('src', 'src'), ('config', 'config')],
    hiddenimports=['psutil', 'pywin32', 'pythonnet', 'pydantic', 'loguru', 'yaml', 'shougun_remote', 'shougun_remote.services', 'shougun_remote.core', 'shougun_remote.config', 'shougun_remote.models', 'shougun_remote.repositories', 'shougun_remote.monitors', 'watchdog', 'watchdog.observers', 'watchdog.events'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ShougunRemoteX_Service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
