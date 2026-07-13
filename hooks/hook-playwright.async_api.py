"""hook-playwright.sync_api.py ile ayni gerekce: playwright'in resmi
async_api hook'unu (driver/ klasorunu filtresiz ekleyen) gecersiz kilar."""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "playwright", include_py_files=False, excludes=["**/driver/**"]
)
