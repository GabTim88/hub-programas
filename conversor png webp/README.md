# Conversor PNG para WebP

Aplicativo desktop simples e minimalista para:

- Selecionar múltiplos arquivos PNG, JPG e JPEG
- Arrastar e soltar arquivos PNG, JPG e JPEG na área principal
- Definir uma pasta de destino
- Converter para WebP
- Redimensionar por pixels ou por porcentagem
- Escolher o nome de saída e sobrescrever ou não arquivos existentes
- Acompanhar o progresso geral e o arquivo atual durante a conversão

## Como executar

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Observações

- O app usa a biblioteca `Pillow` para converter e redimensionar.
- O arrastar-e-soltar usa `tkinterdnd2`. Se o pacote não estiver instalado, o botão de upload continua funcionando normalmente.
