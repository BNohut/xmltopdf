"""playwright'in kendi tasidigi resmi PyInstaller hook'unu (entry point ile
otomatik yuklenir) gecersiz kilar.

Orijinali `collect_data_files("playwright")` ile driver/ klasorunu (node
calistiricisi + Chromium) filtresiz ekliyor. Chromium'un ic ice (.app icinde
.app) yapisi PyInstaller'in otomatik codesign adimini bozdugu icin driver/
klasoru burada haric tutuluyor; xmltopdf.spec derlemeden SONRA bu klasoru
(Google'in kendi imzasini bozmadan) ayri bir adimda kopyalar.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "playwright", include_py_files=False, excludes=["**/driver/**"]
)
