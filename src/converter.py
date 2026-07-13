"""e-Defter berat XML -> PDF donusturme mantigi.

Akis: XML --(XSLT 2.0, berat.xslt)--> HTML --(headless Chromium)--> PDF
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# Paketlenmis (PyInstaller) build'lerde Chromium, playwright paketinin kendi
# icine gomulur (bkz. xmltopdf.spec). PLAYWRIGHT_BROWSERS_PATH=0, playwright'a
# tarayiciyi genel kullanici onbellegi yerine bu gomulu konumdan aramasini
# soyler; ayni deger hem 'playwright install' sirasinda hem burada calisma
# zamaninda kullanilmali. playwright import edilmeden ONCE ayarlanmali.
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from saxonche import PySaxonProcessor  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUTPUT_FOLDER_NAME = "PDF_Ciktilari"


@dataclass
class FileResult:
    xml_path: Path
    pdf_path: Optional[Path]
    success: bool
    error: Optional[str] = None


@dataclass
class ConversionSummary:
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list = field(default_factory=list)


def find_xml_files(root: Path, skip_dir: Optional[Path] = None):
    """Kok dizin altindaki tum .xml dosyalarini (alt klasorler dahil) sirali dondurur."""
    for path in sorted(root.rglob("*.xml")):
        if skip_dir is not None:
            try:
                path.relative_to(skip_dir)
                continue  # cikti klasorunun icindeki dosyalari atla
            except ValueError:
                pass
        if path.is_file():
            yield path


def default_output_root(input_root: Path) -> Path:
    return input_root / OUTPUT_FOLDER_NAME


def build_output_path(xml_path: Path, input_root: Path, output_root: Path) -> Path:
    relative = xml_path.relative_to(input_root).with_suffix(".pdf")
    return output_root / relative


class BeratConverter:
    """XSLT islemcisini ve tarayiciyi bir kere ayaga kaldirip tekrar tekrar kullanir."""

    def __init__(self, xslt_path: Path):
        self.xslt_path = Path(xslt_path)
        self._saxon_cm = None
        self._proc = None
        self._xslt_executable = None
        self._playwright_cm = None
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self):
        self._saxon_cm = PySaxonProcessor(license=False)
        self._proc = self._saxon_cm.__enter__()
        xslt_processor = self._proc.new_xslt30_processor()
        self._xslt_executable = xslt_processor.compile_stylesheet(
            stylesheet_file=str(self.xslt_path)
        )

        self._playwright_cm = sync_playwright()
        self._playwright = self._playwright_cm.__enter__()
        self._browser = self._playwright.chromium.launch()
        self._page = self._browser.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser is not None:
            self._browser.close()
        if self._playwright_cm is not None:
            self._playwright_cm.__exit__(exc_type, exc_val, exc_tb)
        if self._saxon_cm is not None:
            self._saxon_cm.__exit__(exc_type, exc_val, exc_tb)

    def xml_to_html(self, xml_path: Path) -> str:
        return self._xslt_executable.transform_to_string(source_file=str(xml_path))

    def html_to_pdf(self, html: str, pdf_path: Path) -> None:
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        self._page.set_content(html, wait_until="load")
        self._page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
        )

    def convert_file(self, xml_path: Path, pdf_path: Path) -> None:
        html = self.xml_to_html(xml_path)
        self.html_to_pdf(html, pdf_path)


def convert_folder(
    input_root: Path,
    output_root: Optional[Path],
    xslt_path: Path,
    progress_callback: Optional[Callable[[FileResult, int, int], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None,
) -> ConversionSummary:
    """input_root altindaki tum XML dosyalarini bulur, PDF'e cevirir ve
    output_root altina input_root'a gore ayni klasor yapisiyla kaydeder.

    output_root verilmezse input_root icinde 'PDF_Ciktilari' klasoru olusturulur.
    """
    input_root = Path(input_root)
    output_root = Path(output_root) if output_root else default_output_root(input_root)
    output_root.mkdir(parents=True, exist_ok=True)

    skip_dir = output_root if output_root.is_relative_to(input_root) else None

    xml_files = list(find_xml_files(input_root, skip_dir=skip_dir))
    summary = ConversionSummary(total=len(xml_files))

    with BeratConverter(xslt_path) as converter:
        for index, xml_path in enumerate(xml_files, start=1):
            if should_stop is not None and should_stop():
                break

            pdf_path = build_output_path(xml_path, input_root, output_root)
            try:
                converter.convert_file(xml_path, pdf_path)
                result = FileResult(xml_path=xml_path, pdf_path=pdf_path, success=True)
                summary.succeeded += 1
            except Exception as exc:  # noqa: BLE001 - tek dosyadaki hata tum islemi durdurmamali
                result = FileResult(
                    xml_path=xml_path, pdf_path=None, success=False, error=str(exc)
                )
                summary.failed += 1

            summary.results.append(result)
            if progress_callback is not None:
                progress_callback(result, index, summary.total)

    return summary
