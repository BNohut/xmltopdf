"""PyInstaller derlemesi bittikten SONRA calistirilir.

xmltopdf.spec, playwright'in 'driver/' klasorunu (node calistiricisi +
PLAYWRIGHT_BROWSERS_PATH=0 ile onceden indirilmis Chromium) bilerek haric
tutar (bkz. hooks/hook-playwright.*.py): Chromium'un ic ice (.app icinde
.app) yapisi, PyInstaller'in otomatik codesign adimini bozuyor. Bu script o
klasoru derleme ciktisina, dosyalari (ozellikle macOS'ta Google'in kendi
imzasini) bozmadan kopyalar.

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


def find_bundle_playwright_dir(bundle_root: Path) -> Path | None:
    """'playwright' adinda, icinde 'py.typed' bulunan (yani gercekten
    playwright paketinin veri dosyalarinin durdugu) klasoru bulur.

    __init__.py gibi .py dosyalari PYZ arsivine gomuldugu icin diskte gercek
    dosya olarak durmaz; 'py.typed' ise collect_data_files(include_py_files=
    False) ile hep diskte kalir, bu yuzden guvenilir bir referans noktasidir.

    macOS'ta PyInstaller surumune gore Contents/Resources/playwright gercek
    klasor, Contents/Frameworks/playwright ona symlink olabilir (ya da PyInstaller
    surumune gore bunun tersi de olabilir) - hangi yoldan bulunursa bulunsun
    .resolve() ile ayni fiziksel klasore indirgenip tekillestirilir.
    """
    resolved = set()
    for candidate in bundle_root.rglob("playwright"):
        if candidate.is_dir() and (candidate / "py.typed").is_file():
            resolved.add(candidate.resolve())
    if not resolved:
        return None
    if len(resolved) > 1:
        print(f"UYARI: birden fazla playwright klasoru bulundu, ilki kullanilacak: {sorted(resolved)}")
    return sorted(resolved)[0]


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

    playwright_dir = find_bundle_playwright_dir(bundle_root)
    if playwright_dir is None:
        print(f"HATA: {bundle_root} icinde paketlenmis playwright klasoru bulunamadi.")
        return 1

    dest = playwright_dir / "driver"
    print(f"Kopyalaniyor: {driver_src} -> {dest}")

    if sys.platform == "darwin":
        # ditto, .app/.framework yapilarini ve kod imzalarini cp -R'den
        # daha guvenilir korur.
        subprocess.run(["ditto", str(driver_src), str(dest)], check=True)
    else:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(driver_src, dest)

    print("Tamamlandi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
