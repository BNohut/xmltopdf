"""Giris noktasi: e-Defter Berati XML -> PDF Donusturucu GUI'sini baslatir.

Gizli --selftest modu: GUI acmadan, paketlenmis (PyInstaller) binary'nin
XSLT + PDF donusturme hattinin gercekten calistigini dogrular. Pencere
gorunmeyen (windowed) build'lerde stdout gorunmeyebilecegi icin sonuc hem
konsola yazilir hem de bir sonuc dosyasina kaydedilir; CI/otomasyon o dosyayi
okuyarak basari/hata durumunu tespit eder.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def _selftest_output_path() -> Path:
    if "--selftest-out" in sys.argv:
        idx = sys.argv.index("--selftest-out")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])
    return Path.cwd() / "selftest_result.txt"


def run_selftest() -> int:
    import tempfile

    from converter import BeratConverter
    from paths import resources_dir

    out_path = _selftest_output_path()
    res_dir = resources_dir()
    xslt_path = res_dir / "berat.xslt"
    sample_xml = res_dir / "selftest_sample.xml"

    def report(message: str) -> None:
        print(message)
        out_path.write_text(message + "\n", encoding="utf-8")

    if not xslt_path.is_file():
        report(f"SELFTEST FAIL - berat.xslt bulunamadi: {xslt_path}")
        return 1
    if not sample_xml.is_file():
        report(f"SELFTEST FAIL - ornek XML bulunamadi: {sample_xml}")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "selftest.pdf"
        try:
            with BeratConverter(xslt_path) as converter:
                converter.convert_file(sample_xml, pdf_path)
        except Exception as exc:  # noqa: BLE001
            report(f"SELFTEST FAIL - donusturme hatasi: {exc}")
            return 1

        size = pdf_path.stat().st_size if pdf_path.exists() else 0
        if size < 1000:
            report(f"SELFTEST FAIL - PDF cok kucuk veya olusmadi ({size} bayt)")
            return 1

        report(f"SELFTEST OK - PDF basariyla uretildi ({size} bayt)")
        return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(run_selftest())

    from gui import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
