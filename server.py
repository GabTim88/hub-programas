"""
Hub de Programas — Servidor Flask unificado
Serve: Conversor PNG→WebP, Organizador de Pastas
O Gerador de QR é pure JS, não precisa de backend.
"""
import os
import sys
import json
import shutil
import threading
import webbrowser
from pathlib import Path
from tkinter import Tk, filedialog

from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image

# ── Configurações ──────────────────────────────────────────
BASE_DIR = Path(__file__).parent
app = Flask(__name__, static_folder=str(BASE_DIR), template_folder=str(BASE_DIR))
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

ALLOWED_IMG_EXTENSIONS = {".png", ".jpg", ".jpeg"}

EXTENSIONS = {
    ".pdf":  "Arquivos em PDF",
    ".txt":  "Arquivos em TXT",
    ".doc":  "Arquivos de Word",
    ".docx": "Arquivos de Word",
    ".xls":  "Arquivos de Excel",
    ".xlsx": "Arquivos de Excel",
    ".ppt":  "Arquivos de PowerPoint",
    ".pptx": "Arquivos de PowerPoint",
    ".mp3":  "Arquivos de Áudio",
    ".mp4":  "Arquivos de Vídeo",
    ".jpg":  "Arquivos de Imagem",
    ".jpeg": "Arquivos de Imagem",
    ".png":  "Arquivos de Imagem",
    ".zip":  "Arquivos Comprimidos",
    ".rar":  "Arquivos Comprimidos",
    ".7z":   "Arquivos Comprimidos",
}


# ── Utilitários ────────────────────────────────────────────
def open_folder_dialog() -> str:
    """Abre o diálogo de seleção de pasta do Windows via tkinter."""
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder = filedialog.askdirectory(title="Selecionar pasta")
    root.destroy()
    return folder or ""


def open_folder_in_explorer(path: str) -> None:
    """Abre a pasta no Windows Explorer."""
    if sys.platform == "win32":
        os.startfile(path)


# ── CORS headers ───────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ── Rotas estáticas ────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/style.css")
def stylesheet():
    return send_from_directory(str(BASE_DIR), "style.css")


# ── API: Selecionar pasta (tkinter dialog) ─────────────────
@app.route("/api/select-folder", methods=["POST", "OPTIONS"])
def select_folder():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    folder = open_folder_dialog()
    return jsonify({"folder": folder, "success": bool(folder)})


# ── API: Abrir pasta no Explorer ───────────────────────────
@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    try:
        data = request.get_json(force=True)
        folder = data.get("folder", "")
        path = Path(folder)
        if not path.exists():
            return jsonify({"error": "Pasta não encontrada"}), 404
        open_folder_in_explorer(str(path))
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── API: Converter PNG → WebP ──────────────────────────────
@app.route("/api/convert", methods=["POST"])
def convert():
    try:
        if "files" not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "Lista de arquivos vazia"}), 400

        resize_mode  = request.form.get("resize_mode", "original")
        quality      = int(request.form.get("quality", 85))
        output_dir   = request.form.get("output_dir", "").strip()
        percent_val  = int(request.form.get("percent_value", 100))
        width_val    = request.form.get("width_value", "").strip()
        height_val   = request.form.get("height_value", "").strip()

        # Pasta de saída padrão: Downloads do usuário
        if not output_dir:
            output_dir = str(Path.home() / "Downloads")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []
        for file in files:
            suffix = Path(file.filename).suffix.lower()
            if suffix not in ALLOWED_IMG_EXTENSIONS:
                continue
            try:
                img = Image.open(file.stream).convert("RGBA")

                # Redimensionamento
                if resize_mode == "percentage" and percent_val != 100:
                    factor = percent_val / 100
                    img = img.resize(
                        (max(1, int(img.width * factor)), max(1, int(img.height * factor))),
                        Image.Resampling.LANCZOS,
                    )
                elif resize_mode == "pixels":
                    w = int(width_val)  if width_val  else img.width
                    h = int(height_val) if height_val else img.height
                    img = img.resize((w, h), Image.Resampling.LANCZOS)

                # Salvar WebP
                out_name = Path(file.filename).stem + ".webp"
                out_file = _unique_path(output_path / out_name)
                img.save(str(out_file), "WEBP", quality=quality, method=6)

                results.append({
                    "original":  file.filename,
                    "converted": out_file.name,
                    "path":      str(out_file),
                    "success":   True,
                })
            except Exception as exc:
                results.append({"original": file.filename, "success": False, "error": str(exc)})

        return jsonify({"results": results, "count": len(results)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


def _unique_path(candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    i = 1
    while True:
        p = candidate.parent / f"{candidate.stem}_{i}{candidate.suffix}"
        if not p.exists():
            return p
        i += 1


# ── API: Organizar Pastas ──────────────────────────────────
@app.route("/api/organize", methods=["POST"])
def organize():
    try:
        data = request.get_json(force=True)
        folder = data.get("folder", "").strip()

        folder_path = Path(folder)
        if not folder_path.exists():
            return jsonify({"error": "Pasta não encontrada"}), 404

        log_lines = []
        moved = 0
        errors = 0

        # Backup de segurança
        backup_dir = folder_path / "backup_original"
        backup_dir.mkdir(exist_ok=True)
        log_lines.append(f"📁 Pasta de origem: {folder_path}")
        log_lines.append(f"💾 Backup em: {backup_dir}")
        log_lines.append("")

        for item in sorted(folder_path.iterdir()):
            # Ignorar arquivos de sistema e a pasta de backup
            if item.is_dir():
                continue
            if item.name in ("Thumbs.db", ".DS_Store"):
                continue
            if item == backup_dir:
                continue

            ext = item.suffix.lower()
            if ext in EXTENSIONS:
                dest_dir = folder_path / EXTENSIONS[ext]
                dest_dir.mkdir(exist_ok=True)
                dest_file = _unique_path(dest_dir / item.name)
                try:
                    shutil.move(str(item), str(dest_file))
                    log_lines.append(f"✓ Movido: {item.name} → {EXTENSIONS[ext]}")
                    moved += 1
                except Exception as exc:
                    log_lines.append(f"⚠ Erro ao mover {item.name}: {exc}")
                    errors += 1
            else:
                log_lines.append(f"⏭ Ignorado: {item.name}")

        log_lines.append("")
        log_lines.append(f"✅ Concluído: {moved} arquivo(s) organizados, {errors} erro(s).")
        return jsonify({"log": log_lines, "moved": moved, "errors": errors})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Iniciar servidor ───────────────────────────────────────
if __name__ == "__main__":
    import io
    # Fix encoding for Windows terminals that don't support UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    port = 5000

    print()
    print("=" * 55)
    print("  Hub de Programas -- Servidor Local")
    print("=" * 55)
    print(f"  Acesse: http://127.0.0.1:{port}")
    print("  Pressione Ctrl+C para encerrar")
    print("=" * 55)
    print()

    # Abrir o browser automaticamente apos 1s
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    app.run(debug=False, host="127.0.0.1", port=port, use_reloader=False)
