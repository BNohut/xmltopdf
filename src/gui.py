"""e-Defter Berati XML -> PDF Donusturucu - basit masaustu arayuzu (Windows / macOS).

Not: Burada bilincli olarak ttk (temali) widget'lar yerine klasik tkinter
widget'lari kullanilmaktadir. macOS'ta sistemle gelen eski Tk 8.5 surumunde
ttk'nin Aqua tema motoru bozuk oldugu icin butonlar/etiketler görünmez hale
gelebiliyor; klasik tk widget'lari bu sorunu yasamiyor.
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

sys.path.insert(0, str(Path(__file__).resolve().parent))
from converter import OUTPUT_FOLDER_NAME, convert_folder, default_output_root  # noqa: E402
from paths import resources_dir  # noqa: E402

RESOURCES_DIR = resources_dir()
DEFAULT_XSLT_PATH = RESOURCES_DIR / "berat.xslt"

# macOS'ta sistemin eski Tk 8.5 surumu Dark Mode'da metin/arkaplan renklerini
# dogru hesaplayamiyor (yazi görünmez oluyor). Bu yuzden tum renkleri acik
# temaya sabitliyoruz; sistem gorunumunden bagimsiz her zaman okunabilir olur.
BG = "#f0f0f0"
FG = "#000000"
ENTRY_BG = "#ffffff"


class ProgressBar(tk.Frame):
    """ttk.Progressbar yerine kullanilan basit, klasik-Tk tabanli ilerleme cubugu."""

    def __init__(self, master, height=18, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(
            self, height=height, bg="#e5e5e5", highlightthickness=1,
            highlightbackground="#999999",
        )
        self.canvas.pack(fill="x", expand=True)
        self._rect = self.canvas.create_rectangle(0, 0, 0, height, fill="#3b82f6", width=0)
        self._max = 100
        self._value = 0
        self.canvas.bind("<Configure>", lambda _e: self._redraw())

    def set_progress(self, value, maximum=None):
        if maximum is not None:
            self._max = max(maximum, 1)
        self._value = value
        self._redraw()

    def _redraw(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        frac = min(max(self._value / self._max, 0), 1) if self._max else 0
        self.canvas.coords(self._rect, 0, 0, int(width * frac), height)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("e-Defter Berati XML -> PDF Donusturucu")
        self.geometry("720x520")
        self.minsize(640, 440)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.use_default_output = tk.BooleanVar(value=True)
        self.xslt_path = tk.StringVar()
        self.use_default_xslt = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Hazir.")

        self._log_queue: "queue.Queue[str]" = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._stop_requested = False

        self._build_widgets()
        self.after(100, self._drain_log_queue)

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}
        self.configure(bg=BG)

        frame_in = tk.Frame(self, bg=BG)
        frame_in.pack(fill="x", **pad)
        tk.Label(frame_in, text="Kaynak klasor:", bg=BG, fg=FG).pack(side="left")
        tk.Entry(
            frame_in, textvariable=self.input_dir, bg=ENTRY_BG, fg=FG,
            insertbackground=FG, disabledforeground=FG,
        ).pack(side="left", fill="x", expand=True, padx=6)
        tk.Button(
            frame_in, text="Gozat...", command=self._pick_input_dir, bg=BG, fg=FG,
            highlightbackground=BG,
        ).pack(side="left")

        frame_out_toggle = tk.Frame(self, bg=BG)
        frame_out_toggle.pack(fill="x", **pad)
        tk.Checkbutton(
            frame_out_toggle,
            text=f"Ciktiyi kaynak klasorun icinde otomatik olustur ('{OUTPUT_FOLDER_NAME}' klasoru)",
            variable=self.use_default_output,
            command=self._toggle_output_entry,
            bg=BG, fg=FG, selectcolor=ENTRY_BG, activebackground=BG, activeforeground=FG,
        ).pack(side="left")

        self.frame_out = tk.Frame(self, bg=BG)
        self.frame_out.pack(fill="x", **pad)
        tk.Label(self.frame_out, text="Cikti klasoru:", bg=BG, fg=FG).pack(side="left")
        self.output_entry = tk.Entry(
            self.frame_out, textvariable=self.output_dir, bg=ENTRY_BG, fg=FG,
            insertbackground=FG, disabledforeground=FG,
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.output_browse_btn = tk.Button(
            self.frame_out, text="Gozat...", command=self._pick_output_dir, bg=BG, fg=FG,
            highlightbackground=BG,
        )
        self.output_browse_btn.pack(side="left")
        self._toggle_output_entry()

        frame_xslt_toggle = tk.Frame(self, bg=BG)
        frame_xslt_toggle.pack(fill="x", **pad)
        tk.Checkbutton(
            frame_xslt_toggle,
            text="Varsayilan berat.xslt sablonunu kullan (onerilen)",
            variable=self.use_default_xslt,
            command=self._toggle_xslt_entry,
            bg=BG, fg=FG, selectcolor=ENTRY_BG, activebackground=BG, activeforeground=FG,
        ).pack(side="left")

        self.frame_xslt = tk.Frame(self, bg=BG)
        self.frame_xslt.pack(fill="x", **pad)
        tk.Label(self.frame_xslt, text="XSLT sablonu:", bg=BG, fg=FG).pack(side="left")
        self.xslt_entry = tk.Entry(
            self.frame_xslt, textvariable=self.xslt_path, bg=ENTRY_BG, fg=FG,
            insertbackground=FG, disabledforeground=FG,
        )
        self.xslt_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.xslt_browse_btn = tk.Button(
            self.frame_xslt, text="Gozat...", command=self._pick_xslt_file, bg=BG, fg=FG,
            highlightbackground=BG,
        )
        self.xslt_browse_btn.pack(side="left")
        self._toggle_xslt_entry()

        frame_actions = tk.Frame(self, bg=BG)
        frame_actions.pack(fill="x", **pad)
        self.start_btn = tk.Button(
            frame_actions, text="Donusturmeyi Baslat", command=self._start_conversion,
            bg=BG, fg=FG, highlightbackground=BG,
        )
        self.start_btn.pack(side="left")
        self.cancel_btn = tk.Button(
            frame_actions, text="Iptal", command=self._cancel_conversion, state="disabled",
            bg=BG, fg=FG, highlightbackground=BG,
        )
        self.cancel_btn.pack(side="left", padx=6)

        self.progress = ProgressBar(self, bg=BG)
        self.progress.pack(fill="x", **pad)

        tk.Label(self, textvariable=self.status_text, anchor="w", bg=BG, fg=FG).pack(
            anchor="w", fill="x", padx=10
        )

        self.log_widget = scrolledtext.ScrolledText(
            self, state="disabled", wrap="word", bg=ENTRY_BG, fg=FG, insertbackground=FG,
        )
        self.log_widget.pack(fill="both", expand=True, padx=10, pady=(6, 10))

    def _toggle_output_entry(self):
        state = "disabled" if self.use_default_output.get() else "normal"
        self.output_entry.configure(state=state)
        self.output_browse_btn.configure(state=state)

    def _toggle_xslt_entry(self):
        state = "disabled" if self.use_default_xslt.get() else "normal"
        self.xslt_entry.configure(state=state)
        self.xslt_browse_btn.configure(state=state)

    def _pick_input_dir(self):
        chosen = filedialog.askdirectory(title="Kaynak klasoru secin")
        if chosen:
            self.input_dir.set(chosen)

    def _pick_output_dir(self):
        chosen = filedialog.askdirectory(title="Cikti klasoru secin")
        if chosen:
            self.output_dir.set(chosen)

    def _pick_xslt_file(self):
        chosen = filedialog.askopenfilename(
            title="XSLT sablonu secin",
            filetypes=[("XSLT dosyalari", "*.xslt *.xsl"), ("Tum dosyalar", "*.*")],
        )
        if chosen:
            self.xslt_path.set(chosen)

    def _log(self, message: str):
        self._log_queue.put(message)

    def _drain_log_queue(self):
        try:
            while True:
                message = self._log_queue.get_nowait()
                self.log_widget.configure(state="normal")
                self.log_widget.insert("end", message + "\n")
                self.log_widget.see("end")
                self.log_widget.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _start_conversion(self):
        input_dir = self.input_dir.get().strip()
        if not input_dir:
            messagebox.showwarning("Eksik bilgi", "Once bir kaynak klasor secin.")
            return
        input_path = Path(input_dir)
        if not input_path.is_dir():
            messagebox.showerror("Hata", "Secilen kaynak klasor bulunamadi.")
            return

        if self.use_default_xslt.get():
            xslt_path = DEFAULT_XSLT_PATH
            if not xslt_path.is_file():
                messagebox.showerror(
                    "Eksik dosya",
                    f"berat.xslt bulunamadi: {xslt_path}",
                )
                return
        else:
            xslt_dir = self.xslt_path.get().strip()
            if not xslt_dir:
                messagebox.showwarning("Eksik bilgi", "Bir XSLT sablonu secin.")
                return
            xslt_path = Path(xslt_dir)
            if not xslt_path.is_file():
                messagebox.showerror("Hata", "Secilen XSLT dosyasi bulunamadi.")
                return

        if self.use_default_output.get():
            output_path = default_output_root(input_path)
        else:
            output_dir = self.output_dir.get().strip()
            if not output_dir:
                messagebox.showwarning("Eksik bilgi", "Bir cikti klasoru secin.")
                return
            output_path = Path(output_dir)

        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", "end")
        self.log_widget.configure(state="disabled")

        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._stop_requested = False
        self.status_text.set("Donusturme basladi...")
        self.progress.set_progress(0, maximum=100)

        self._worker_thread = threading.Thread(
            target=self._run_conversion,
            args=(input_path, output_path, xslt_path),
            daemon=True,
        )
        self._worker_thread.start()

    def _cancel_conversion(self):
        self._stop_requested = True
        self.status_text.set("Iptal isteniyor, mevcut dosya bitince duracak...")

    def _run_conversion(self, input_path: Path, output_path: Path, xslt_path: Path):
        def on_progress(result, index, total):
            self.progress.set_progress(index, maximum=max(total, 1))
            rel = result.xml_path.relative_to(input_path)
            if result.success:
                self._log(f"[{index}/{total}] OK  -> {rel}")
            else:
                self._log(f"[{index}/{total}] HATA -> {rel} :: {result.error}")
            self.status_text.set(f"{index}/{total} tamamlandi")

        try:
            summary = convert_folder(
                input_root=input_path,
                output_root=output_path,
                xslt_path=xslt_path,
                progress_callback=on_progress,
                should_stop=lambda: self._stop_requested,
            )
        except Exception as exc:  # noqa: BLE001
            self._log(f"Beklenmeyen hata: {exc}")
            self.after(0, self._on_finished_error, str(exc))
            return

        self.after(0, self._on_finished, summary, output_path)

    def _on_finished(self, summary, output_path: Path):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_text.set(
            f"Bitti: {summary.succeeded} basarili, {summary.failed} hatali (toplam {summary.total})"
        )
        messagebox.showinfo(
            "Tamamlandi",
            f"Toplam {summary.total} dosya islendi.\n"
            f"Basarili: {summary.succeeded}\nHatali: {summary.failed}\n\n"
            f"Ciktilar: {output_path}",
        )

    def _on_finished_error(self, error_message: str):
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_text.set("Hata olustu.")
        messagebox.showerror("Hata", error_message)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
