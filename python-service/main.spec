# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para PDF Converter Service.
Genera un ejecutable único para Windows.

Uso:
    pyinstaller main.spec
"""

from PyInstaller.utils.hooks import collect_data_files
import os

block_cipher = None

# Obtener ruta base
BASE_PATH = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['app/main.py'],
    pathex=[BASE_PATH],
    binaries=[],
    datas=[],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'structlog',
        'structlog.stdlib',
        'pydantic',
        'pydantic_settings',
        'fitz',
        'polars',
        'xlsxwriter',
        'anyio',
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy.testing',
        'pytest',
        'IPython',
        'jupyter',
    ],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True para ver logs en consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Agregar icono si se desea: icon='icon.ico'
)
