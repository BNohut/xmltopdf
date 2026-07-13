# e-Defter Berati XML -> PDF Donusturucu

Verilen bir kok klasoru ve altindaki tum alt klasorleri gezer, icindeki e-Defter
berat XML dosyalarini bulur ve GIB'in resmi `berat.xslt` sablonunu kullanarak
resmi gorunumde PDF'e cevirir. Ciktilar, kaynak klasorun icinde olusturulan
`PDF_Ciktilari` klasorune, kaynaktaki ile ayni alt klasor yapisi korunarak
kaydedilir.

Ornek: `Kaynak/2022/Ocak/berat.xml` -> `Kaynak/PDF_Ciktilari/2022/Ocak/berat.pdf`

Windows ve macOS'ta calisir. Basit bir masaustu penceresi (Tkinter) uzerinden
kullanilir.

## Kullanicilar icin (Python kurmaya gerek yok)

Programin, cift tiklayip acabileceginiz hazir paketlenmis surumleri var:
- macOS: `e-Defter Berati Donusturucu-macOS.zip`
- Windows: `e-Defter Berati Donusturucu-Windows.zip`

Bu dosyalari [GitHub deposunun "Releases" sayfasindan](https://github.com/BNohut/xmltopdf/releases)
indirebilirsiniz (depo su an private oldugu icin GitHub hesabinizin depoya
davet edilmis olmasi gerekir). Alternatif olarak, depoya erisimi olan biri
"Actions" sekmesindeki en son basarili calismanin ciktilarini indirip size
dogrudan (e-posta, Drive vb.) da gonderebilir; indirdiginiz zip dosyasinin
kendisi tamamen bagimsizdir, sonrasinda GitHub'a veya internete ihtiyac
duymaz.

Kurulum adimlari:
1. Zip dosyasini indirin ve cikarin (cift tiklamak genelde yeterlidir).
2. **macOS**: cikan `e-Defter Berati Donusturucu.app` dosyasina cift tiklayin.
3. **Windows**: cikan klasorun icindeki `e-Defter Berati Donusturucu.exe`
   dosyasina cift tiklayin.

### macOS: "Taninmayan gelistirici" uyarisi

Program bir Apple Developer hesabiyla imzalanmadigi icin (bkz. asagidaki not)
ilk acilista macOS Gatekeeper bunu engeller. Cozumu:

1. `.app` dosyasina **sag tiklayin** (veya Control tusuna basili tutup
   tiklayin), acilan menuden **"Ac"** secin.
2. Cikan uyari penceresinde tekrar **"Ac"** butonuna basin.

Eger bu menude "Ac" secenegi yoksa veya hala engelleniyorsa: **Sistem
Ayarlari > Gizlilik ve Guvenlik** yolunu acin, asagi kaydirin, uygulamanin
adinin yaninda cikan **"Yine de Ac"** butonuna basin.

Bu onay sadece ilk acilista bir kere gerekir; sonraki aciliste tekrar
sormaz.

### Windows: "Windows bilgisayarinizi korudu" (SmartScreen) uyarisi

Program bir kod imzalama sertifikasiyla imzalanmadigi icin SmartScreen ilk
calistirmada uyarir. Cozumu:

1. Uyari penceresinde **"Daha fazla bilgi"** (More info) baglantisina
   tiklayin.
2. Cikan **"Yine de calistir"** (Run anyway) butonuna tiklayin.

### Boyut ve ilk acilis hakkinda

Paket, icine gomulu bir tarayici (Chromium headless-shell, PDF olusturmak
icin) ve bir XSLT motoru icerdigi icin indirme boyutu buyukce (zip olarak
macOS'ta ~175 MB, Windows'ta ~205 MB). Bu sayede kurulumdan sonra **internet
baglantisina gerek kalmaz** - tum bilesenler paketin icindedir. Ilk acilista
bilgisayarin hizina gore bir-iki saniye surebilir, bu normaldir.

## Programin kullanimi

Acilan pencerede:

1. "Gozat..." ile XML dosyalarinin bulundugu kok klasoru secin.
2. Varsayilan olarak cikti, kaynak klasorun icinde `PDF_Ciktilari` adiyla
   olusturulur. Farkli bir yer istiyorsaniz ust kutucuktaki isareti kaldirip
   kendi cikti klasorunuzu secebilirsiniz.
3. Varsayilan olarak pakete gomulu `berat.xslt` sablonu kullanilir. Farkli
   (ornegin guncellenmis) bir sablonla donusturmek isterseniz "Varsayilan
   berat.xslt sablonunu kullan" isaretini kaldirip kendi `.xslt`/`.xsl`
   dosyanizi secebilirsiniz.
4. "Donusturmeyi Baslat" butonuna basin. Ilerleme ve olasi hatalar alt
   kisimdaki listede gorunur; islem sirasinda pencere kilitlenmez.
5. Bitince ozet (kac dosya basarili/hatali) bir pencerede gosterilir.

Bir dosyada hata olusursa (ornegin XML bozuksa veya sema disi bir yapidaysa)
islem durmaz, o dosya "hatali" olarak isaretlenip diger dosyalarla devam edilir.

## Nasil calisir (teknik ozet)

1. XML, GIB'in resmi `resources/berat.xslt` sablonuyla (XSLT 2.0, Saxon-HE ile)
   HTML'e donusturulur.
2. HTML, headless Chromium (Playwright) ile PDF'e basilir. Bu sayede resmi
   goruntu birebir korunur.
3. Imza (`ds:Signature`) alanlari sadece bilgi olarak gosterilir; kriptografik
   dogrulama yapilmaz.

## Farkli bir berat.xslt kullanmak

`resources/berat.xslt` dosyasini kendi surumunuzle degistirebilirsiniz; program
her zaman bu dosyayi kullanir.

---

## Gelistiriciler icin

### Kaynak koddan calistirma

**Onemli (macOS):** macOS'un sistemle gelen Python'u ve bazen Homebrew
Python da, cok eski bir Tcl/Tk (8.5, 2012) ile geliyor. Bu eski surum modern
macOS'ta ciddi bir grafik hatasina neden oluyor: pencere aciliyor ama
icindeki hicbir yazi/buton/kutu gorunmuyor (bos/siyah pencere). Bu yuzden
[python.org](https://www.python.org/downloads/macos/)'dan resmi Python
kurucusunu (universal2 installer, guncel Tcl/Tk 8.6+ ile gelir)
kullanmanizi tavsiye ederiz. Bu kurulum mevcut Homebrew/sistem/pyenv
Python'larinizin yanina, bagimsiz ve ek olarak kurulur; onlari degistirmez
veya bozmaz.

```bash
cd xmltopdf
# <surum> yerine kurdugunuz surumu yazin (ornek: 3.13)
/Library/Frameworks/Python.framework/Versions/<surum>/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python run.py
```

Windows (PowerShell):

```powershell
cd xmltopdf
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
python run.py
```

### Sorun giderme (macOS, kaynaktan calistirma)

- **`ModuleNotFoundError: No module named '_tkinter'`**: Kullandiginiz
  Python'da tkinter kurulu degil (siklikla Homebrew Python'da olur).
  Yukaridaki python.org kurulumuna gecin.
- **Pencere aciliyor ama icinde hicbir sey gorunmuyor / bos-siyah
  gorunuyor**: Sistem/Homebrew Python'un eski Tcl/Tk 8.5 surumunun modern
  macOS'ta bilinen bir grafik/repaint hatasidir; kod tarafinda
  duzeltilemez. Cozum: python.org'dan guncel Python kurup `.venv` klasorunu
  o Python ile yeniden olusturun. `python -c "import tkinter; print(tkinter.TkVersion)"`
  ile `8.6` veya uzeri gormelisiniz.

### Tek tikla acilan paket (.app / .exe) uretmek

Paketleme PyInstaller ile yapilir; `xmltopdf.spec` bunu tanimlar. Iki native
bagimlilik ozel dikkat gerektirir:

- **saxonche**: native `.dylibs` (macOS) / DLL (Windows) dosyalari spec
  icinde otomatik bulunup dogru yerlesimle pakete eklenir.
- **playwright**: gomulu Chromium'un ic ice (.app icinde .app) yapisi
  PyInstaller'in otomatik codesign adimini bozdugu icin, `hooks/` klasorundeki
  ozel hook'lar bu klasoru pakete DAHIL ETMEZ; `packaging/copy_playwright_driver.py`
  derlemeden SONRA bu klasoru (orijinal imzalar bozulmadan) ayri bir adimda
  kopyalar.

Yerel derleme (calisiyorsaniz zaten `.venv` icindesiniz):

```bash
pip install -r requirements-build.txt
PLAYWRIGHT_BROWSERS_PATH=0 python -m playwright install chromium
pyinstaller xmltopdf.spec --noconfirm
python packaging/copy_playwright_driver.py "dist/e-Defter Berati Donusturucu.app"   # macOS
# Windows'ta: python packaging/copy_playwright_driver.py "dist/e-Defter Berati Donusturucu"

# Dogrulama (GUI acmadan pipeline'in calistigini kontrol eder):
"dist/e-Defter Berati Donusturucu.app/Contents/MacOS/e-Defter Berati Donusturucu" --selftest
```

**Otomatik derleme (GitHub Actions):** `.github/workflows/build.yml`,
`main`'e her push'ta veya `v*.*.*` seklinde bir tag push'landiginda hem
macOS (Apple Silicon/arm64) hem Windows paketini otomatik derler, her ikisini
de `--selftest` ile dogrular ve sonuclari "Actions" sekmesinde artifact
olarak, tag push'unda ayrica "Releases" sayfasinda yayinlar. Manuel
tetiklemek icin: Actions sekmesi -> "Paketleri derle" -> "Run workflow".

> Not: Bir Apple Developer hesabi olmadigi icin macOS paketi code sign +
> notarize edilmemistir; bu yuzden kullanicilar yukaridaki Gatekeeper
> adimini izlemek zorunda. Windows tarafinda da bir kod imzalama sertifikasi
> yok, SmartScreen uyarisi cikar. Ileride bir imzalama sertifikasi
> edinilirse `xmltopdf.spec`'teki `codesign_identity`/`entitlements_file`
> alanlari ve CI workflow'u guncellenerek bu uyarilar tamamen kaldirilabilir.

### Proje yapisi

```
xmltopdf/
  run.py                        # giris noktasi (+ gizli --selftest modu)
  requirements.txt               # calisma zamani bagimliliklari
  requirements-build.txt         # + pyinstaller (paketleme icin)
  xmltopdf.spec                  # PyInstaller yapilandirmasi
  hooks/                         # playwright'in resmi hook'larini gecersiz kilan ozel hook'lar
  packaging/
    copy_playwright_driver.py    # derleme sonrasi Chromium/driver kopyalama adimi
  resources/
    berat.xslt                   # GIB resmi e-Defter berat XSLT sablonu
    selftest_sample.xml          # --selftest icin kucuk ornek XML
  src/
    converter.py                 # XML tarama + XSLT + PDF donusturme mantigi
    gui.py                       # Tkinter arayuzu
    paths.py                     # kaynak/paketlenmis modda dogru resources/ yolunu bulur
  .github/workflows/build.yml    # macOS + Windows otomatik derleme
```
