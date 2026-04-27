# -*- mode: python ; coding: utf-8 -*-
# AIAT.spec - правильная упаковка с ctransformers
# Запуск: pyinstaller AIAT.spec --clean

import os
import sys
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Собираем бинарники ctransformers (.dll, .pyd, .so)
ctransformers_binaries = []
try:
    import ctransformers
    ct_dir = os.path.dirname(ctransformers.__file__)
    print(f"[SPEC] ctransformers: {ct_dir}")
    for pattern in ['*.dll', '*.pyd', '*.so', '**/*.dll', '**/*.pyd', '**/*.so']:
        for f in glob.glob(os.path.join(ct_dir, pattern), recursive=True):
            rel = os.path.relpath(f, os.path.dirname(ct_dir))
            dest = os.path.dirname(rel)
            ctransformers_binaries.append((f, dest))
            print(f"[SPEC] bin: {f} -> {dest}")
except Exception as e:
    print(f"[SPEC] ctransformers error: {e}")

ctransformers_datas = []
try:
    ctransformers_datas = collect_data_files('ctransformers')
except:
    pass

torch_datas = []
try:
    torch_datas = collect_data_files('torch')
except:
    pass

a = Analysis(
    ['AIAT.py'],
    pathex=['.'],
    binaries=ctransformers_binaries,
    datas=[
        *collect_data_files('kivymd'),
        *collect_data_files('kivy'),
        *collect_data_files('PIL'),
        *ctransformers_datas,
        *torch_datas,
    ],
    hiddenimports=[
        'kivy',
        'kivy.core.window',
        'kivy.core.window.window_sdl2',
        'kivy.core.text',
        'kivy.core.text.text_sdl2',
        'kivy.core.image',
        'kivy.core.audio',
        'kivy.core.audio.audio_sdl2',
        'kivy.core.clipboard',
        'kivy.core.clipboard.clipboard_winctypes',
        'kivy.storage',
        'kivy.storage.jsonstore',
        'kivy.graphics',
        'kivy.graphics.cgl_backend',
        'kivy.graphics.cgl_backend.cgl_glew',
        'kivymd',
        'kivymd.app',
        'kivymd.uix.button',
        'kivymd.uix.screen',
        'kivymd.uix.boxlayout',
        'kivymd.uix.toolbar',
        'kivymd.uix.selectioncontrol',
        'kivymd.uix.slider',
        'kivymd.uix.label',
        'kivymd.uix.textfield',
        'kivymd.uix.card',
        'kivymd.uix.filemanager',
        'kivymd.uix.dialog',
        'kivymd.uix.menu',
        'kivymd.uix.list',
        'ctransformers',
        'ctransformers.models',
        'ctransformers.lib',
        'torch',
        'torch.package',
        'torch.package.package_importer',
        'sounddevice',
        'soundfile',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pyttsx3',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'requests',
        'numpy',
        'tkinter',
        'json',
        'multiprocessing',
        'queue',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas',
        'notebook', 'IPython', 'cv2', 'sklearn',
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
    [],
    exclude_binaries=True,
    name='AIAT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/inko1.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AIAT',
)