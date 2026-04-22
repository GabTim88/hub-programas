import os
import threading
import queue
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - optional dependency
    DND_FILES = None
    TkinterDnD = None


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}

if TkinterDnD is not None:
    BaseTk = TkinterDnD.Tk
else:
    BaseTk = tk.Tk


@dataclass
class ImageItem:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name


class PngToWebpApp(BaseTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PNG para WebP")
        self.geometry("920x620")
        self.minsize(820, 560)

        self.items: list[ImageItem] = []
        self.output_dir = tk.StringVar(value="")
        self.resize_mode = tk.StringVar(value="original")
        self.name_mode = tk.StringVar(value="Manter nome original")
        self.overwrite_existing = tk.BooleanVar(value=False)
        self.width_value = tk.StringVar(value="")
        self.height_value = tk.StringVar(value="")
        self.percent_value = tk.StringVar(value="100")
        self.quality_value = tk.IntVar(value=85)
        self.keep_aspect = tk.BooleanVar(value=True)
        self.current_file_text = tk.StringVar(value="Arquivo atual: nenhum")
        self.status_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._setup_style()
        self._build_ui()
        self.after(120, self._poll_status_queue)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f4f2")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f4f2", foreground="#1f1f1f", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#f4f4f2", foreground="#111111", font=("Segoe UI Semibold", 18))
        style.configure("Subtitle.TLabel", background="#f4f4f2", foreground="#666666", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#111111", font=("Segoe UI Semibold", 11))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#666666", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI Semibold", 10), padding=(14, 8))
        style.map("Accent.TButton", foreground=[("active", "#ffffff"), ("!disabled", "#ffffff")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)
        style.configure("Horizontal.TScale", background="#ffffff")

        self.configure(bg="#f4f4f2")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 14))

        ttk.Label(header, text="Conversor PNG para WebP", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Selecione arquivos, ajuste o redimensionamento e escolha a pasta de saída.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1, uniform="cols")
        body.columnconfigure(1, weight=1, uniform="cols")
        body.rowconfigure(0, weight=1)

        left = ttk.Frame(body, style="Card.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ttk.Frame(body, style="Card.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._build_upload_card(left)
        self._build_settings_card(right)

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(14, 0))
        self.progress = ttk.Progressbar(footer, mode="determinate")
        self.progress.pack(fill="x")
        self.status_label = ttk.Label(footer, text="Pronto para converter.")
        self.status_label.pack(anchor="w", pady=(8, 0))

    def _build_upload_card(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Arquivos", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Clique para selecionar múltiplas imagens PNG, JPG ou JPEG.", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        drop_zone = tk.Frame(parent, bg="#f8f8f6", highlightbackground="#d7d7d2", highlightthickness=1, height=120)
        drop_zone.pack(fill="x")
        drop_zone.pack_propagate(False)
        drop_zone.bind("<Button-1>", lambda _e: self.add_files())
        self._register_drop_target(drop_zone)

        drop_label = tk.Label(
            drop_zone,
            text="Clique aqui ou arraste imagens PNG, JPG ou JPEG aqui",
            bg="#f8f8f6",
            fg="#444444",
            font=("Segoe UI Semibold", 11),
            justify="center",
        )
        drop_label.pack(expand=True)
        drop_label.bind("<Button-1>", lambda _e: self.add_files())
        self._register_drop_target(drop_label)

        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(12, 10))
        ttk.Button(actions, text="Adicionar arquivos", style="Accent.TButton", command=self.add_files).pack(side="left")
        ttk.Button(actions, text="Limpar lista", command=self.clear_files).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(parent)
        list_frame.pack(fill="both", expand=True)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.file_list = tk.Listbox(
            list_frame,
            activestyle="none",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7d7d2",
            relief="flat",
            selectbackground="#dbe7d9",
            selectforeground="#111111",
            font=("Segoe UI", 10),
        )
        self.file_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

    def _build_settings_card(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Configurações", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Defina destino, tamanho e qualidade do WebP.", style="Muted.TLabel").pack(anchor="w", pady=(2, 12))

        output_row = ttk.Frame(parent)
        output_row.pack(fill="x", pady=(0, 10))
        output_row.columnconfigure(0, weight=1)
        ttk.Label(output_row, text="Destino").grid(row=0, column=0, sticky="w")
        ttk.Button(output_row, text="Escolher pasta", command=self.choose_output_dir).grid(row=0, column=1, sticky="e")
        ttk.Label(output_row, textvariable=self.output_dir, style="Muted.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        naming_box = ttk.Frame(parent)
        naming_box.pack(fill="x", pady=(4, 10))
        ttk.Label(naming_box, text="Nome do arquivo").grid(row=0, column=0, sticky="w")
        self.name_mode_combo = ttk.Combobox(
            naming_box,
            state="readonly",
            values=["Manter nome original", "Adicionar sufixo"],
            textvariable=self.name_mode,
        )
        self.name_mode_combo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        naming_box.columnconfigure(0, weight=1)
        ttk.Checkbutton(naming_box, text="Sobrescrever arquivos existentes", variable=self.overwrite_existing).grid(row=2, column=0, sticky="w", pady=(6, 0))

        resize_box = ttk.Frame(parent)
        resize_box.pack(fill="x", pady=(8, 10))
        ttk.Label(resize_box, text="Redimensionamento").grid(row=0, column=0, sticky="w", columnspan=3)

        ttk.Radiobutton(resize_box, text="Manter original", value="original", variable=self.resize_mode, command=self._sync_resize_ui).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Radiobutton(resize_box, text="Por pixels", value="pixels", variable=self.resize_mode, command=self._sync_resize_ui).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        ttk.Radiobutton(resize_box, text="Por porcentagem", value="percent", variable=self.resize_mode, command=self._sync_resize_ui).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(6, 0))

        self.resize_inputs = ttk.Frame(parent)
        self.resize_inputs.pack(fill="x", pady=(0, 10))
        self.resize_inputs.columnconfigure(0, weight=1)
        self.resize_inputs.columnconfigure(1, weight=1)

        self.pixels_panel = ttk.Frame(self.resize_inputs)
        self.pixels_panel.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.pixels_panel.columnconfigure(0, weight=1)
        self.pixels_panel.columnconfigure(1, weight=1)
        ttk.Label(self.pixels_panel, text="Largura (px)").grid(row=0, column=0, sticky="w")
        ttk.Label(self.pixels_panel, text="Altura (px)").grid(row=0, column=1, sticky="w")
        ttk.Entry(self.pixels_panel, textvariable=self.width_value).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Entry(self.pixels_panel, textvariable=self.height_value).grid(row=1, column=1, sticky="ew")

        self.percent_panel = ttk.Frame(self.resize_inputs)
        self.percent_panel.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.percent_panel.columnconfigure(0, weight=1)
        ttk.Label(self.percent_panel, text="Porcentagem de redução").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.percent_panel, textvariable=self.percent_value).grid(row=1, column=0, sticky="ew")
        ttk.Label(self.percent_panel, text="Ex.: 50 reduz a imagem pela metade.", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(4, 0))

        self.keep_aspect_widget = ttk.Checkbutton(parent, text="Manter proporção", variable=self.keep_aspect)
        self.keep_aspect_widget.pack(anchor="w")

        quality_box = ttk.Frame(parent)
        quality_box.pack(fill="x", pady=(12, 0))
        ttk.Label(quality_box, text=f"Qualidade WebP: {self.quality_value.get()}").pack(anchor="w")
        self.quality_label = quality_box.winfo_children()[0]
        self.quality_slider = ttk.Scale(
            quality_box,
            from_=30,
            to=100,
            orient="horizontal",
            command=self._on_quality_change,
        )
        self.quality_slider.set(self.quality_value.get())
        self.quality_slider.pack(fill="x", pady=(6, 0))

        current_file_box = ttk.Frame(parent)
        current_file_box.pack(fill="x", pady=(12, 0))
        ttk.Label(current_file_box, textvariable=self.current_file_text, style="Muted.TLabel").pack(anchor="w")
        self.current_file_progress = ttk.Progressbar(current_file_box, mode="determinate", maximum=100)
        self.current_file_progress.pack(fill="x", pady=(6, 0))

        convert_row = ttk.Frame(parent)
        convert_row.pack(fill="x", pady=(18, 0))
        ttk.Button(convert_row, text="Converter para WebP", style="Accent.TButton", command=self.start_conversion).pack(side="left")
        ttk.Button(convert_row, text="Abrir pasta", command=self.open_output_dir).pack(side="left", padx=(8, 0))

        note = ttk.Label(
            parent,
            text="Dica: se você quiser apenas converter sem redimensionar, deixe os campos de tamanho vazios.",
            style="Muted.TLabel",
            wraplength=360,
            justify="left",
        )
        note.pack(anchor="w", pady=(18, 0))

        self._sync_resize_ui()

    def _on_quality_change(self, value: str) -> None:
        quality = int(float(value))
        self.quality_value.set(quality)
        self.quality_label.configure(text=f"Qualidade WebP: {quality}")

    def _sync_resize_ui(self) -> None:
        mode = self.resize_mode.get()
        if mode == "pixels":
            self.pixels_panel.grid()
            self.percent_panel.grid_remove()
            self.keep_aspect_widget.configure(state="normal")
        elif mode == "percent":
            self.percent_panel.grid()
            self.pixels_panel.grid_remove()
            self.keep_aspect_widget.configure(state="disabled")
        else:
            self.pixels_panel.grid_remove()
            self.percent_panel.grid_remove()
            self.keep_aspect_widget.configure(state="disabled")

    def _register_drop_target(self, widget: tk.Widget) -> None:
        if TkinterDnD is None:
            return
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", self._handle_drop)

    def _handle_drop(self, event: tk.Event) -> None:
        if not getattr(event, "data", None):
            return

        if hasattr(self.tk, "splitlist"):
            raw_paths = self.tk.splitlist(event.data)
        else:
            raw_paths = (event.data,)

        added = 0
        for raw in raw_paths:
            path = Path(raw)
            if path.is_dir():
                for child in sorted(path.iterdir()):
                    added += self._try_add_path(child)
            else:
                added += self._try_add_path(path)

        if added:
            self.set_status(f"{added} arquivo(s) adicionados por arrastar-e-soltar.")

    def _try_add_path(self, path: Path) -> int:
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS or not path.exists():
            return 0
        if any(existing.path == path for existing in self.items):
            return 0
        self.items.append(ImageItem(path=path))
        self.file_list.insert(tk.END, path.name)
        return 1

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecionar imagens",
            filetypes=[("Imagens PNG/JPG", "*.png *.jpg *.jpeg"), ("Todos os arquivos", "*.*")],
        )
        if not paths:
            return

        added = 0
        for raw in paths:
            added += self._try_add_path(Path(raw))

        if added == 0:
            self.set_status("Nenhuma imagem nova foi adicionada.")
        else:
            self.set_status(f"{added} arquivo(s) adicionados.")

    def clear_files(self) -> None:
        self.items.clear()
        self.file_list.delete(0, tk.END)
        self.set_status("Lista limpa.")

    def choose_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Escolher pasta de destino")
        if not folder:
            return
        self.output_dir.set(folder)
        self.set_status("Pasta de destino selecionada.")

    def open_output_dir(self) -> None:
        folder = self.output_dir.get().strip()
        if not folder:
            messagebox.showinfo("Destino", "Escolha uma pasta de destino primeiro.")
            return
        os.startfile(folder)

    def start_conversion(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Conversão em andamento", "Aguarde a conversão atual terminar.")
            return

        if not self.items:
            messagebox.showwarning("Sem arquivos", "Adicione pelo menos uma imagem PNG, JPG ou JPEG.")
            return

        output_dir = self.output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("Sem destino", "Escolha a pasta de destino antes de converter.")
            return

        target = Path(output_dir)
        if not target.exists():
            messagebox.showwarning("Destino inválido", "A pasta de destino não existe.")
            return

        try:
            resize_mode = self.resize_mode.get()
            width = self._parse_int(self.width_value.get())
            height = self._parse_int(self.height_value.get())
            percent = self._parse_percent(self.percent_value.get())
            quality = int(self.quality_value.get())
        except ValueError as exc:
            messagebox.showwarning("Configuração inválida", str(exc))
            return

        self.progress["value"] = 0
        self.progress["maximum"] = len(self.items)
        self.current_file_text.set("Arquivo atual: aguardando...")
        self.current_file_progress["value"] = 0
        self.set_status("Convertendo imagens...")

        self.worker_thread = threading.Thread(
            target=self._convert_worker,
            args=(
                target,
                quality,
                resize_mode,
                width,
                height,
                percent,
                self.keep_aspect.get(),
                self.name_mode.get(),
                self.overwrite_existing.get(),
            ),
            daemon=True,
        )
        self.worker_thread.start()

    def _convert_worker(
        self,
        output_dir: Path,
        quality: int,
        resize_mode: str,
        width: int | None,
        height: int | None,
        percent: int | None,
        keep_aspect: bool,
        name_mode: str,
        overwrite_existing: bool,
    ) -> None:
        try:
            converted = 0
            for index, item in enumerate(self.items, start=1):
                self.status_queue.put(("current", item.name))
                with Image.open(item.path) as img:
                    img = img.convert("RGBA")
                    img = self._resize_image(img, resize_mode, width, height, percent, keep_aspect)
                    out_path = self._build_output_path(output_dir, item.path, name_mode, overwrite_existing)
                    img.save(out_path, "WEBP", quality=quality, method=6)

                converted += 1
                self.status_queue.put(("progress", f"Convertido: {item.name}"))
                self.status_queue.put(("current_done", item.name))
                self.status_queue.put(("step", str(index)))

            self.status_queue.put(("done", f"{converted} imagem(ns) convertida(s) com sucesso."))
        except Exception as exc:  # noqa: BLE001
            self.status_queue.put(("error", str(exc)))

    def _build_output_path(self, output_dir: Path, source_path: Path, name_mode: str, overwrite_existing: bool) -> Path:
        stem = source_path.stem
        if name_mode == "Adicionar sufixo":
            filename = f"{stem}_webp.webp"
        else:
            filename = f"{stem}.webp"

        candidate = output_dir / filename
        if overwrite_existing or not candidate.exists():
            return candidate

        counter = 1
        while True:
            candidate = output_dir / f"{candidate.stem}_{counter}.webp"
            if not candidate.exists():
                return candidate
            counter += 1

    def _resize_image(
        self,
        img: Image.Image,
        mode: str,
        width: int | None,
        height: int | None,
        percent: int | None,
        keep_aspect: bool,
    ) -> Image.Image:
        if mode == "original":
            return img

        current_width, current_height = img.size

        if mode == "percent":
            factor = (percent or 100) / 100
            if factor <= 0:
                raise ValueError("A porcentagem precisa ser maior que zero.")
            new_size = (
                max(1, int(current_width * factor)),
                max(1, int(current_height * factor)),
            )
            if factor == 1:
                return img
            return img.resize(new_size, Image.Resampling.LANCZOS)

        if width is None and height is None:
            return img

        if keep_aspect:
            target_width = width or current_width
            target_height = height or current_height

            if mode == "exact":
                ratio = min(target_width / current_width, target_height / current_height)
                new_size = (
                    max(1, int(current_width * ratio)),
                    max(1, int(current_height * ratio)),
                )
            else:
                img_copy = img.copy()
                img_copy.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
                return img_copy
        else:
            new_size = (
                width or current_width,
                height or current_height,
            )

        return img.resize(new_size, Image.Resampling.LANCZOS)

    def _parse_int(self, value: str) -> int | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        number = int(cleaned)
        if number <= 0:
            raise ValueError("Os valores de largura e altura precisam ser maiores que zero.")
        return number

    def _parse_percent(self, value: str) -> int | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        number = int(cleaned)
        if number <= 0:
            raise ValueError("A porcentagem precisa ser maior que zero.")
        return number

    def _poll_status_queue(self) -> None:
        while True:
            try:
                kind, payload = self.status_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "progress":
                self.set_status(payload)
            elif kind == "current":
                self.current_file_text.set(f"Arquivo atual: {payload}")
                self.current_file_progress["value"] = 0
            elif kind == "current_done":
                self.current_file_progress["value"] = 100
            elif kind == "step":
                self.progress["value"] = float(payload)
            elif kind == "done":
                self.progress["value"] = self.progress["maximum"]
                self.set_status(payload)
                self.current_file_text.set("Arquivo atual: concluído")
                messagebox.showinfo("Concluído", payload)
            elif kind == "error":
                self.set_status("Falha na conversão.")
                self.current_file_text.set("Arquivo atual: erro")
                messagebox.showerror("Erro", payload)

        self.after(120, self._poll_status_queue)

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)


if __name__ == "__main__":
    app = PngToWebpApp()
    app.mainloop()
