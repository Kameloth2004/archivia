# ArchivIA — Inventário universal por extensão

Atualizado em 2026-11-21. **Implementado em código, aguardando validação no Windows.**

## Objetivo

Expandir o bibliotecário de mídias para **todos os arquivos regulares** acessíveis em uma árvore de diretórios, preservando a categorização original de imagem/vídeo/áudio e os snapshots SQLite existentes.

## Categorias

- `imagem`: JPG, JPEG, PNG, GIF, WebP, AVIF, SVG, TIFF, RAW e outras extensões de imagem já conhecidas.
- `video`: MP4, MOV, AVI, MKV, WebM e similares.
- `audio`: MP3, WAV, FLAC, AAC e similares.
- `documento`: PDF, TXT, DOC, DOCX, ODT, RTF, MD, EPUB.
- `planilha`: XLS, XLSX, XLSM, ODS, CSV, TSV.
- `apresentacao`: PPT, PPTX, ODP, PPS, PPSX.
- `compactado`: ZIP, RAR, 7Z, TAR, GZ, BZ2, XZ, TGZ.
- `codigo`: PY, PHP, JS, TS, HTML, CSS, JSON, XML, YAML, SQL, SH, PS1 e outras extensões de código listadas em `inventory.py`.
- `outro`: todas as extensões não classificadas, inclusive arquivos sem extensão.

Identificação **apenas pela extensão**, não pelo conteúdo. PDFs são classificados como documentos mesmo que contenham imagens. ZIPs são identificados como um arquivo, sem abrir/descompactar ou examinar seu interior. Pastas chamadas `BACKUPS` são varridas normalmente se forem diretórios reais; não significam, por si, leitura interna de arquivos ZIP.

## Semântica dos campos e compatibilidade

O `inventory()` preserva os campos históricos:
- `media_files`: quantidade exclusiva de imagens + vídeos + áudios.
- `bytes_media`: bytes exclusivos das três categorias de mídia.
- `other_files`: quantidade de arquivos de outras categorias (inclusive desconhecidos).
- `by_category`: total por cada categoria.

Adiciona:
- `indexed_files`: quantidade de **todos os arquivos** encontrados, inclusive `outro`.
- `bytes_indexed`: bytes de todos os arquivos encontrados.

A tabela SQLite `media` **continua com o nome histórico** para não exigir migração destrutiva; novos snapshots também gravam documentos e outros tipos nesta tabela. A tabela `scans` mantém campos históricos, e `catalog_summary()` deriva `indexed_files` e `bytes_indexed` por agregação das linhas reais de cada snapshot. Snapshots antigos seguem representando somente as mídias então conhecidas e **não são retroativamente enriquecidos**. Para atualizar um diretório, catalogar novamente quando um fluxo de gravação for liberado. Neste momento, a GUI continua em prévia, sem gravação.

## Segurança e desempenho

- Sem ler bytes de arquivos ou abrir arquivos compactados.
- Sem alterar, mover ou renomear arquivos.
- Links simbólicos continuam ignorados.
- Inventário completo ainda é mantido em RAM; GUI pagina só a exibição (50 linhas).
- Modelos de IA/agent tool calling **não** ganham automaticamente permissão para mover novas categorias: a simulação de movimentação mantém somente imagem/vídeo/áudio por enquanto.
- Todos os testes sintéticos em `tests/`.

## Validação no Windows

```bash
cd /d/PROJETOS/archivia
git pull origin main
python -m unittest discover -s tests -v
archivia-gui
```

Na GUI, selecionar `D:/IW8 CONSTRUMAQ`, clicar **Examinar pasta — prévia**, verificar que **Arquivos** supera ou iguala **Mídias** e testar filtro `Documentos`, `Compactados`, `Código-fonte`. Não existe necessidade de regravar o SQLite nesse teste.

## Evoluções futuras

Seleção configurável de categorias e exclusões, histórico por origem, inventário incremental e streaming; inspeção opcional e segura de arquivos compactados, com limites de tamanho, profundidade e arquivos; classificação semântica com Ollama. Nenhuma dessas funções foi implementada nesta etapa.
