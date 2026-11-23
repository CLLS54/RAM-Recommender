# -*- mode: python ; coding: utf-8 -*-
"""
RAMRecommender.spec - dos objetivos desde un solo build:

  dist/RAMRecommender.exe        GUI tkinter (sin consola)  <- src/app_gui.py
  dist/RAMRecommender-cli.exe    consola                    <- src/cli.py

Build:  python -m PyInstaller RAMRecommender.spec
"""
import os

# SPECPATH es una variable inyectada por PyInstaller (no existe __file__ en el spec).
HERE = SPECPATH
SRC = os.path.join(HERE, "src")

# Icono del ejecutable (multi-size 16..256 px, PNG dentro de contenedor ICO).
ICON = os.path.join(HERE, "assets", "ram.ico")

# Datos que el binario necesita en tiempo de ejecucion (sys._MEIPASS).
DATAS = [
    (os.path.join(HERE, "data", "dram_dies.json"), "data"),
    (os.path.join(HERE, "bench", "membench.exe"), "bench"),
]

# Modules importados solo de forma dinamica o indirecta.
HIDDEN = [
    "tkinter",
    "argparse",
    "json",
    "glob",
    "subprocess",
    "datetime",
    "re",
    "difflib",
    # Modulos propios importados de forma dinamica o desde funciones:
    # hwmatch decide plataforma/VDIMM y valida snapshots; hwsys lee el
    # hardware en Windows/macOS/Linux; memprofile arma el perfil actual;
    # cpuz lee los timings activos con CPU-Z; spd_live identifica el die por
    # part number (recommend.identify_die lo importa en local).
    "hwmatch",
    "hwsys",
    "memprofile",
    "spd_live",
    "sync11",
    "bench",
    "doctor",
    "cpuz",
]


def analyze(entry):
    return Analysis(
        [os.path.join(SRC, entry)],
        pathex=[SRC],
        binaries=[],
        datas=DATAS,
        hiddenimports=HIDDEN,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )


def make_exe(pyz, analysis, name, console, icon=None):
    return EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,          # UPX detectado en C:\Users\Soporte\AppData\Local\Microsoft\WinGet\Links\upx.EXE
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon,
    )


a_gui = analyze("app_gui.py")
a_cli = analyze("cli.py")

pyz_gui = PYZ(a_gui.pure)
pyz_cli = PYZ(a_cli.pure)

ICO = ICON if os.path.exists(ICON) else None
exe_gui = make_exe(pyz_gui, a_gui, "RAMRecommender", False, icon=ICO)
exe_cli = make_exe(pyz_cli, a_cli, "RAMRecommender-cli", True, icon=ICO)
