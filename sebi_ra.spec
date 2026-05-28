# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'data' / 'app_constants.json'), 'data'),
        (str(ROOT / 'config_example.json'), '.'),
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        'telethon',
        'telethon.errors',
        'telethon.tl.types',
        'telethon.tl.functions',
        'SmartApi',
        'pyotp',
        'gspread',
        'openpyxl',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'google.oauth2.service_account',
        'google.auth',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'psd_tools',
        'photoshop',
        'image_generation_rough',
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'icecream',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SEBI_RA_Automation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='SEBI_RA_Automation',
)

# --- Updater EXE (standalone, no console window) ---
updater_a = Analysis(
    ['updater.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        'telethon',
        'SmartApi',
        'pyotp',
        'gspread',
        'openpyxl',
        'PIL',
        'google.oauth2',
        'google.auth',
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'icecream',
        'psd_tools',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

updater_pyz = PYZ(updater_a.pure, cipher=block_cipher)

updater_exe = EXE(
    updater_pyz,
    updater_a.scripts,
    updater_a.binaries,
    updater_a.datas,
    [],
    name='updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)