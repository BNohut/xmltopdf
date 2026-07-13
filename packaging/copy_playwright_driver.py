"""PyInstaller derlemesi bittikten SONRA calistirilir.

xmltopdf.spec, playwright'in 'driver/' klasorunu (node calistiricisi +
PLAYWRIGHT_BROWSERS_PATH=0 ile onceden indirilmis Chromium) bilerek haric
tutar (bkz. hooks/hook-playwright.*.py ve spec'teki _without_playwright_driver
guvenlik filtresi): Chromium'un ic ice (.app icinde .app) yapisi,
PyInstaller'in otomatik codesign adimini bozuyor. Bu script o klasoru
derleme ciktisina, dosyalari (ozellikle macOS'ta Google'in kendi imzasini)
bozmadan kopyalar.

Hedef klasor, PyInstaller'in dokumante ettigi sabit yerlesime gore
DOGRUDAN hesaplanir (bir "playwright" klasoru aramaya calismak, ayni
klasorun bazi PyInstaller surumlerinde birden fazla - biri bozuk/yaridan
kalma - kopyasinin olusabilmesi yuzunden guvenilir degil):
  - macOS (.app):      <bundle>.app/Contents/Resources   (sys._MEIPASS ile ayni)
  - Windows (onedir):  <bundle>/_internal                (sys._MEIPASS ile ayni)

Kullanim:
    python packaging/copy_playwright_driver.py "dist/<AppName>.app"   (macOS)
    python packaging/copy_playwright_driver.py "dist/<AppName>"       (Windows, onedir)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import playwright


def meipass_equivalent(bundle_root: Path) -> Path:
    if sys.platform == "darwin":
        return bundle_root / "Contents" / "Resources"
    return bundle_root / "_internal"


# Playwright 'chromium' kurulduğunda beraberinde birkac bagimsiz bilesim
# daha indirir, ama biz sadece duz p.chromium.launch() (headless=True,
# kanal belirtmeden) + page.pdf() kullaniyoruz. Test ederek dogrulandi:
# - "chromium-*" (tam Chrome for Testing, ~344 MB): launch(headless=True)
#   ozel bir kanal belirtilmedigi surece BUNU DEGIL, headless-shell'i
#   kullaniyor - kullanilmiyor.
# - "ffmpeg-*": sadece video kaydi (record_video_dir) icin, hic kullanilmiyor.
# "chromium_headless_shell-*" GERCEKTEN kullanildigi icin (asil PDF uretimi
# bunun uzerinden yapiliyor) buraya DAHIL EDILMEDI.
UNUSED_BROWSER_GLOBS = ["chromium-*", "ffmpeg-*"]


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def prune_unused_browsers(driver_dest: Path) -> None:
    local_browsers = driver_dest / "package" / ".local-browsers"
    if not local_browsers.is_dir():
        return
    for pattern in UNUSED_BROWSER_GLOBS:
        for match in local_browsers.glob(pattern):
            if match.is_dir():
                size_mb = _dir_size(match) / 1024 / 1024
                print(f"Kullanilmayan tarayici cikariliyor: {match.name} ({size_mb:.0f} MB)")
                shutil.rmtree(match)


def main() -> int:
    if len(sys.argv) != 2:
        print("Kullanim: copy_playwright_driver.py <paketlenmis-app-klasoru>")
        return 1

    bundle_root = Path(sys.argv[1]).resolve()
    if not bundle_root.exists():
        print(f"HATA: bulunamadi: {bundle_root}")
        return 1

    driver_src = Path(playwright.__file__).resolve().parent / "driver"
    if not driver_src.is_dir():
        print(f"HATA: playwright driver klasoru bulunamadi: {driver_src}")
        print(
            "Once 'PLAYWRIGHT_BROWSERS_PATH=0 python -m playwright install "
            "chromium' calistirin."
        )
        return 1

    base = meipass_equivalent(bundle_root)
    if not base.is_dir():
        print(f"HATA: beklenen taban klasor bulunamadi: {base}")
        return 1

    dest = base / "playwright" / "driver"
    print(f"Kopyalaniyor: {driver_src} -> {dest}")

    # Onceki (basarisiz) bir derleme denemesinden veya PyInstaller'in kismi
    # dahil ettigi bir kalinti varsa, temiz baslamak icin once silinir.
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()

    dest.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "darwin":
        # ditto, .app/.framework yapilarini ve kod imzalarini cp -R'den
        # daha guvenilir korur.
        subprocess.run(["ditto", str(driver_src), str(dest)], check=True)
        prune_unused_browsers(dest)

        # PyInstaller, BUNDLE adiminda .app'i ZATEN imzalamisti (icindekilerin
        # bir "muhur"unu olusturdu). Buraya sonradan dosya eklemek o muhuru
        # gecersiz kilar ve Gatekeeper "is damaged and can't be opened" der
        # (codesign --verify: "a sealed resource is missing or invalid").
        # Cozum: TUM icerik eklendikten SONRA butun bundle'i --deep ile
        # yeniden imzalamak. --deep, ic ice Chrome.app/Framework yapisini da
        # kendi (bagimsiz gecerli) imzasiyla birlikte dogru sekilde
        # isliyor - PyInstaller'in kendi otomatik, tek-tek-Mach-O imzalama
        # adiminin (bkz. spec dosyasindaki _without_playwright_driver notu)
        # aksine.
        print(f"Yeniden imzalaniyor (ad-hoc, --deep): {bundle_root}")
        subprocess.run(
            ["codesign", "--force", "--deep", "--sign", "-", str(bundle_root)],
            check=True,
        )
        verify = subprocess.run(
            ["codesign", "--verify", "--deep", "--strict", str(bundle_root)],
            capture_output=True,
            text=True,
        )
        if verify.returncode != 0:
            print(f"HATA: yeniden imzalama sonrasi dogrulama basarisiz:\n{verify.stderr}")
            return 1
        print("Imza dogrulandi.")
    else:
        shutil.copytree(driver_src, dest)
        prune_unused_browsers(dest)

    print("Tamamlandi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
