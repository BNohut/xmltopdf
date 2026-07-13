# e-Defter Berati XML -> PDF Donusturucu

Verilen bir kok klasoru ve altindaki tum alt klasorleri gezer, icindeki e-Defter
berat XML dosyalarini bulur ve GIB'in resmi `berat.xslt` sablonunu kullanarak
resmi gorunumde PDF'e cevirir. Ciktilar, kaynak klasorun icinde olusturulan
`PDF_Ciktilari` klasorune, kaynaktaki ile ayni alt klasor yapisi korunarak
kaydedilir.

Ornek: `Kaynak/2022/Ocak/berat.xml` -> `Kaynak/PDF_Ciktilari/2022/Ocak/berat.pdf`

Windows ve macOS'ta calisir. Basit bir masaustu penceresi (Tkinter) uzerinden
kullanilir; komut satiri bilgisi gerekmez.

## Nasil calisir (teknik ozet)

1. XML, GIB'in resmi `resources/berat.xslt` sablonuyla (XSLT 2.0, Saxon-HE ile)
   HTML'e donusturulur.
2. HTML, headless Chromium (Playwright) ile PDF'e basilir. Bu sayede resmi
   goruntu birebir korunur.
3. Imza (`ds:Signature`) alanlari sadece bilgi olarak gosterilir; kriptografik
   dogrulama yapilmaz.

## Kurulum

### macOS

**Onemli:** macOS'un sistemle gelen Python'u ve bazen Homebrew Python da, cok
eski bir Tcl/Tk (8.5, 2012) ile geliyor. Bu eski surum modern macOS'ta ciddi
bir grafik hatasina neden oluyor: pencere aciliyor ama icindeki hicbir yazi/
buton/kutu gorunmuyor (bos/siyah pencere), veya donusturme sirasinda log
guncellenmiyormus gibi gorunuyor. Bu yuzden [python.org](https://www.python.org/downloads/macos/)'dan
resmi Python kurucusunu (universal2 installer, guncel Tcl/Tk 8.6+ ile gelir)
kullanmanizi tavsiye ederiz. Bu kurulum mevcut Homebrew/sistem/pyenv Python'larinizin
yanina, bagimsiz ve ek olarak kurulur; onlari degistirmez veya bozmaz.

```bash
cd xmltopdf
# <surum> yerine kurdugunuz surumu yazin (ornek: 3.13)
/Library/Frameworks/Python.framework/Versions/<surum>/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Windows (PowerShell)

```powershell
cd xmltopdf
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

> Not: `playwright install chromium` adimi ilk kurulumda ~150-200MB bir tarayici
> indirir. Sadece bir kere calistirmaniz yeterli.

## Sorun giderme (macOS)

- **`ModuleNotFoundError: No module named '_tkinter'`**: Kullandiginiz Python'da
  tkinter kurulu degil (siklikla Homebrew Python'da olur). Yukaridaki
  python.org kurulumuna gecin.
- **Pencere aciliyor ama icinde hicbir sey gorunmuyor / bos-siyah gorunuyor,
  ya da donusturme sirasinda log alani guncellenmiyormus gibi duruyor**: Bu,
  sistem/Homebrew Python'un eski Tcl/Tk 8.5 surumunun modern macOS'ta bilinen
  bir grafik/repaint hatasidir; kod tarafinda duzeltilemez. Cozum: yukaridaki
  gibi python.org'dan guncel Python kurup `.venv` klasorunu o Python ile
  yeniden olusturun (`rm -rf .venv` sonra yukaridaki adimlari tekrarlayin).
  Kurulan Python'un modern bir Tk ile geldigini `python -c "import tkinter;
  print(tkinter.TkVersion)"` ile dogrulayabilirsiniz; `8.6` veya uzeri
  gormelisiniz (`8.5` ise sorun devam eder).

## Calistirma

```bash
# macOS
.venv/bin/python run.py

# Windows
.venv\Scripts\python.exe run.py
```

Acilan pencerede:

1. "Gozat..." ile XML dosyalarinin bulundugu kok klasoru secin.
2. Varsayilan olarak cikti, kaynak klasorun icinde `PDF_Ciktilari` adiyla
   olusturulur. Farkli bir yer istiyorsaniz ust kutucuktaki isareti kaldirip
   kendi cikti klasorunuzu secebilirsiniz.
3. "Donusturmeyi Baslat" butonuna basin. Ilerleme ve olasi hatalar alt
   kisimdaki listede gorunur; islem sirasinda pencere kilitlenmez.
4. Bitince ozet (kac dosya basarili/hatali) bir pencerede gosterilir.

Bir dosyada hata olusursa (ornegin XML bozuksa veya sema disi bir yapidaysa)
islem durmaz, o dosya "hatali" olarak isaretlenip diger dosyalarla devam edilir.

## Farkli bir berat.xslt kullanmak

`resources/berat.xslt` dosyasini kendi surumunuzle degistirebilirsiniz; program
her zaman bu dosyayi kullanir.

## Proje yapisi

```
xmltopdf/
  run.py                  # giris noktasi
  requirements.txt
  resources/berat.xslt    # GIB resmi e-Defter berat XSLT sablonu
  src/
    converter.py          # XML tarama + XSLT + PDF donusturme mantigi
    gui.py                # Tkinter arayuzu
```
