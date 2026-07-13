# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: e-Defter Berati XML -> PDF Donusturucu.

Hem macOS (.app) hem Windows (.exe) icin calisir; hangi platformda
calistirilirsa o platforma uygun saxonche native kutuphanelerini otomatik
bulup paketler.

Derlemeden once:
    pip install -r requirements.txt
    pip install pyinstaller pyinstaller-hooks-contrib
    PLAYWRIGHT_BROWSERS_PATH=0 python -m playwright install chromium

Derlemek icin:
    pyinstaller xmltopdf.spec --noconfirm
"""

import os
from pathlib import Path

import saxonche
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = Path(SPECPATH).resolve()  # noqa: F821 - PyInstaller spec globals
APP_NAME = "e-Defter Berati Donusturucu"

block_cipher = None

# ---- saxonche native kutuphaneleri (platforma gore farkli yerlesim) ----
saxonche_pkg_dir = Path(saxonche.__file__).resolve().parent
saxonche_binaries = []

# macOS: bagimli dylib'ler "saxonche.dylibs" alt klasorunde durur; ana .so
# @loader_path/saxonche.dylibs/... ile onlara erisir, bu yuzden alt klasor
# yapisi korunmali.
mac_dylibs_dir = saxonche_pkg_dir / "saxonche.dylibs"
if mac_dylibs_dir.is_dir():
    for f in mac_dylibs_dir.iterdir():
        if f.is_file():
            saxonche_binaries.append((str(f), "saxonche.dylibs"))

# Windows: bagimli DLL'ler .pyd ile ayni klasorde (site-packages kokunde)
# duz halde durur; Windows'un varsayilan "ayni klasor" DLL arama sirasina
# guvenebilmek icin onlari da bundle kokune (".") koyuyoruz.
if os.name == "nt":
    for f in saxonche_pkg_dir.iterdir():
        name = f.name.lower()
        if f.is_file() and name.endswith(".dll") and (
            name.startswith("msvcp140-")
            or name.startswith("saxonc-core-he-")
            or name.startswith("saxonc-he-")
        ):
            saxonche_binaries.append((str(f), "."))

# ---- playwright ----
# playwright kendi resmi PyInstaller hook'unu paket icinde tasir (entry point
# ile otomatik yuklenir) ve bu hook 'driver/' klasorunu (node calistiricisi +
# PLAYWRIGHT_BROWSERS_PATH=0 ile onceden indirilmis Chromium) filtresiz
# ekliyor. Chromium'un ic ice (.app icinde .app) yapisi PyInstaller'in
# otomatik codesign adimini bozdugu icin, hooks/hook-playwright.sync_api.py
# ile bu resmi hook'u (ayni isimle) gecersiz kilip driver/ klasorunu haric
# tutuyoruz. O klasor derlemeden SONRA ayri bir adimda (build_mac.py /
# build_windows.py), Google'in kendi imzasi bozulmadan kopyalanir.
playwright_hiddenimports = collect_submodules("playwright")

a = Analysis(
    ["run.py"],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=saxonche_binaries,
    datas=[
        (str(PROJECT_ROOT / "resources"), "resources"),
    ],
    hiddenimports=["saxonche"] + playwright_hiddenimports,
    hookspath=[str(PROJECT_ROOT / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)


def _without_playwright_driver(entries):
    """hooks/hook-playwright.*.py bazi PyInstaller/surum kombinasyonlarinda
    gecersiz kilinmayabiliyor (birden fazla hook kaynagi ayni ada sahip
    olabiliyor). Bu yuzden hangi hook eklemis olursa olsun, TOC'a son bir
    guvenlik agi olarak 'driver' gecen her girdiyi (node calistiricisi +
    Chromium) burada temizliyoruz; o klasor derlemeden SONRA
    packaging/copy_playwright_driver.py ile ayri kopyalanacak."""
    return [
        entry
        for entry in entries
        if "driver" not in entry[0].replace("\\", "/").lower()
        and "driver" not in entry[1].replace("\\", "/").lower()
    ]


a.datas = _without_playwright_driver(a.datas)
a.binaries = _without_playwright_driver(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=None,
    bundle_identifier="com.xmltopdf.edefterberatidonusturucu",
)
