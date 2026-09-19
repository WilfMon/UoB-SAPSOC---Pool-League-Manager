# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Client/main.py'],
    pathex=['Client'],
    binaries=[],
    datas=[
        ('Client/database/league.db', 'database'),
        ('Client/database/schema.sql', 'database'),
        ('Client/resources/', 'resources'),
        ('Client/ui/', 'ui'),
        ('Client/utils/', 'utils'),
        ('Client/settings.json', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyClientApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Set to True if you want a terminal window to pop up for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)