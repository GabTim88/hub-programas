# ⚡ Hub de Programas

> Dashboard local moderno para centralizar ferramentas Python do dia a dia — sem instalação extra, sem complicação.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-black?logo=flask)
![Pillow](https://img.shields.io/badge/Pillow-10.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Sobre

O **Hub de Programas** é uma interface web local (dark mode) que reúne três ferramentas utilitárias em um único lugar, acessíveis diretamente pelo navegador. O backend é um servidor Flask leve que roda localmente na porta `5000`.

---

## 🛠️ Ferramentas disponíveis

### 🖼️ Conversor PNG → WebP
Converta imagens **PNG, JPG ou JPEG** para o formato **WebP** de forma rápida e configurável.

- Upload por clique ou **drag & drop**
- Redimensionamento: original, porcentagem ou pixels fixos
- Controle de qualidade (1–100)
- Seleção de pasta de saída via diálogo nativo do Windows
- Suporte a múltiplos arquivos simultâneos

### 📁 Organizador de Pastas
Organize automaticamente arquivos bagunçados em subpastas por tipo de extensão.

- Seleção de pasta via diálogo nativo
- Backup automático em `backup_original/`
- Log detalhado de cada arquivo movido
- Tipos suportados: PDF, DOC, DOCX, TXT, XLS, XLSX, PPT, PPTX, MP3, MP4, JPG, PNG, ZIP, RAR, 7Z

### 📷 Gerador de QR Code
Gere QR Codes a partir de qualquer texto ou URL, 100% offline (puro JavaScript).

- Configuração de tamanho (px) e margem
- Escolha de cores do QR e do fundo
- Níveis de correção de erro: L, M, Q, H
- Download em **PNG** ou **SVG**
- Atalho `Ctrl+Enter` para gerar rapidamente

---

## 🚀 Como usar

### Pré-requisitos
- [Python 3.10+](https://python.org/downloads/) instalado e no PATH
- Conexão com a internet (apenas para o primeiro `pip install`)

### Instalação e execução

**Opção 1 — Atalho `.bat` (recomendado)**
```
Clique duas vezes em iniciar_hub.bat
```
O script instala as dependências automaticamente e abre o navegador.

**Opção 2 — Manual**
```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
python server.py
```

Acesse **http://127.0.0.1:5000** no navegador.

---

## 📁 Estrutura do projeto

```
Hub de programas/
├── index.html          # Interface web (HTML + CSS + JS inline)
├── style.css           # Estilos globais (dark mode)
├── server.py           # Backend Flask (API + servidor de arquivos estáticos)
├── requirements.txt    # Dependências Python
├── iniciar_hub.bat     # Script de inicialização para Windows
└── README.md
```

---

## ⚙️ Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python · Flask |
| Processamento de imagens | Pillow (PIL) |
| Diálogos nativos | tkinter |
| Frontend | HTML5 · CSS3 · JavaScript (Vanilla) |
| Geração de QR | [qrcodejs](https://github.com/davidshimjs/qrcodejs) |

---

## 📦 Dependências

```txt
flask>=3.0
Pillow>=10.0
```

> `tkinter` já vem incluso na instalação padrão do Python para Windows.

---

## 🪟 Compatibilidade

| Sistema | Suporte |
|---------|---------|
| Windows 10/11 | ✅ Completo |
| macOS | ⚠️ Parcial (diálogo de pasta pode não funcionar) |
| Linux | ⚠️ Parcial (requer `python3-tk`) |

---

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

<p align="center">
  Feito com ☕ e Python
</p>
