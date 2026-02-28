# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('frontend/dist', 'frontend/dist'), ('docs/manuals', 'docs/manuals'), ('unicon/config.yaml', 'unicon')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off'],
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
    name='UniCon_Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UniCon_Desktop',
)
app = BUNDLE(
    coll,
    name='UniCon_Desktop.app',
    icon=None,
    bundle_identifier=None,
)
