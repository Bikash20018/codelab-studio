# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['codelab_studio.py'],
    pathex=[],
    binaries=[],
    # assets/msix is packaging art for the Store manifest, not runtime data:
    # name the two runtime images instead of the whole folder.
    datas=[('assets/app.ico', 'assets'), ('assets/app.png', 'assets'),
           ('tools', 'tools'), ('licenses', 'licenses')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='CodeLabStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX drops the relocation table, which turns ASLR off and is exactly what
    # the Windows App Certification Kit flags.  An MSIX is compressed anyway.
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CodeLabStudio',
)
