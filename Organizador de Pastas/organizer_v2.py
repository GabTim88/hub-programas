#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Organizador de Arquivos por Tipo (Versão .exe)
Cria pastas por tipo (PDF, TXT, XLSX, MP3, MP4, DOC, etc.)
e move os arquivos para a pasta correta.
"""

import os
import shutil
import argparse
import platform
from pathlib import Path
from tkinter import Tk, filedialog

# Definir tipos de arquivos e suas pastas
EXTENSIONS = {
    '.pdf': 'Arquivos em PDF',
    '.txt': 'Arquivos em txt',
    '.doc': 'Aquivos de Word',
    '.docx': 'Arquivos deWord',
    '.xls': 'Arquivos de Excel',
    '.xlsx': 'Arquivos de Excel',
    '.ppt': 'Arquivos de PowerPoint',
    '.pptx': 'Arquivos dePowerPoint',
    '.mp3': 'Arquivos em mp3',
    '.mp4': 'Arquivos em mp4',
    '.jpg': 'Arquivos de Imagem',
    '.jpeg': 'Arquivos de Imagem',
    '.png': 'Arquivos de Imagem',
    '.zip': 'Arquivo Comprimido',
    '.rar': 'Arquivo Comprimido',
    '.7z': 'Arquivo Comprimido',
}

def select_folder():
    """Seleciona a pasta de origem via GUI"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title="Selecione a pasta para organizar")
    root.destroy()
    return folder

def organize_files(folder_path, confirm=True):
    """Organiza arquivos por tipo em subpastas"""
    folder_path = Path(folder_path)
    if not folder_path.exists():
        print(f"❌ Pasta '{folder_path}' não existe.")
        return

    # Criar pasta de backup caso tenha erros
    backup_dir = folder_path / "backup_original"
    backup_dir.mkdir(exist_ok=True)
    print(f"🗂️  Pasta de origem: {folder_path}")
    print(f"📁  Pasta de backup: {backup_dir}\n")

    # Variáveis para controle
    processed_count = 0
    error_count = 0

    # Percorrer todos os arquivos (ignorar .py, .log, etc.)
    for item in folder_path.iterdir():
        if item.is_file() and item.name != '.DS_Store' and item.name != 'Thumbs.db':
            ext = item.suffix.lower()

            if ext in EXTENSIONS:
                type_folder = folder_path / EXTENSIONS[ext]
                # Criar pasta do tipo se não existir
                type_folder.mkdir(exist_ok=True)
                # Nome único para arquivo duplicado
                target_path = type_folder / f"{item.stem}{ext}"
                # Evitar sobrescrita
                count = 1
                while target_path.exists():
                    count += 1
                    target_path = type_folder / f"{item.stem}_{count}{ext}"
                # Mover arquivo
                try:
                    shutil.move(str(item), str(target_path))
                    print(f"✓ Movido: {item.name} → {type_folder.name}")
                    processed_count += 1
                except Exception as e:
                    print(f"⚠️  Erro ao mover {item.name}: {e}")
                    shutil.copy2(str(item), str(backup_dir / f"{item.name}"))
                    error_count += 1
            else:
                print(f"⏭️  Ignorado: {item.name} (tipo: {ext})")

    print(f"\n✅ Conclusão: {processed_count} arquivos organizados")
    print(f"⚠️  Erros: {error_count} arquivos movidos para backup")
    print(f"📁  Pasta de backup: {backup_dir}\n")

    # Confirmação automática
    if confirm:
        print("✅ Confirmação automática: operação concluída.")
    else:
        print("⚠️  Confirmação automática: operação cancelada.")

def main():
    """Função principal"""
    print("=" * 60)
    print("🛠️  Organizador de Arquivos por Tipo")
    print("=" * 60)
    print("Tipos suportados: PDF, TXT, DOC, XLSX, PPT, MP3, MP4, JPG, ZIP...\n")

    # Usar argparse para receber parâmetros de linha de comando
    parser = argparse.ArgumentParser(description="Organizador de Arquivos por Tipo")
    parser.add_argument("folder", help="Pasta de origem")
    parser.add_argument("--confirm", action="store_true", default=True, help="Confirmar operação")

    args = parser.parse_args()
    folder_path = args.folder
    confirm = args.confirm

    # Se não houver confirmação, o script continua automaticamente
    organize_files(folder_path, confirm=confirm)

if __name__ == "__main__":
    main()
