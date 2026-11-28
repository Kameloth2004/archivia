# Catálogo de funções de produção — parte 3/3

Referência: `Kameloth2004/archivia`, branch `feat/v2-video-thumbnails-2026-11-27`, commit `2afb6c97edff83cadd013136ea1573ee3b66aaf9` (28/11/2026). **DOC** = descrição literal da primeira linha da docstring, **INFERÊNCIA** = responsabilidade inferida do nome e assinatura; nenhuma inferência certifica ausência de efeitos colaterais. Inclui métodos privados, especiais e funções aninhadas.

## `src/archivia/manual_pilot.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 27 | `_check_plain()` | Responsável por  check plain, conforme a implementação **[INFERÊNCIA]** |
| 37 | `_read_hash()` | Responsável por  read hash, conforme a implementação **[INFERÊNCIA]** |
| 70 | `preview_manual_copy()` | Exige raiz com subpastas 'origem' e 'destino', sem criar diretórios. **[DOC]** |
| 94 | `_journal()` | Responsável por  journal, conforme a implementação **[INFERÊNCIA]** |
| 105 | `prepare_manual_copy()` | Publica uma cópia verificada; a imagem de origem jamais é apagada. **[DOC]** |

## `src/archivia/metadata/__init__.py`

Sem funções definidas.

## `src/archivia/metadata/exiftool_adapter.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 20 | `available_exiftool()` | O ExifTool é opt-in pela instalação local no PATH. **[DOC]** |
| 25 | `extract_exiftool()` | Devolve grupos legíveis; a única execução externa é o leitor local. **[DOC]** |

## `src/archivia/metadata/reader.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 28 | `_display()` | Representa qualquer valor sem censurá-lo, com truncamento declarado. **[DOC]** |
| 58 | `_image_groups()` | Responsável por  image groups, conforme a implementação **[INFERÊNCIA]** |
| 177 | `_raw_xmp_sections()` | Acesso ao pacote original também quando ExifTool interpreta as tags. **[DOC]** |
| 188 | `read_file_metadata()` | Consulta explicitamente um arquivo regular, sem escrita. **[DOC]** |
| 280 | `_finalize()` | Compatibilidade com a GUI antiga e representação legível estruturada. **[DOC]** |
| 307 | `format_metadata_report()` | Agrupa os campos para leitura profissional em ambos os painéis Qt. **[DOC]** |

## `src/archivia/metadata/xmp_reader.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 18 | `is_xmp_key()` | Responsável por is xmp key, conforme a implementação **[INFERÊNCIA]** |
| 22 | `_decoded()` | Responsável por  decoded, conforme a implementação **[INFERÊNCIA]** |
| 30 | `parse_xmp()` | Retorna grupos estruturados e a seção XML original, sem filtros. **[DOC]** |
| 60 | `qname()` | Responsável por qname, conforme a implementação **[INFERÊNCIA]** |
| 117 | `xmp_from_image_info()` | Extrai todas as entradas XMP conhecidas do dicionário do Pillow. **[DOC]** |

## `src/archivia/move_executor.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 37 | `preview_conflict_move()` | Responsável por preview conflict move, conforme a implementação **[INFERÊNCIA]** |
| 83 | `move_one_approved()` | Responsável por move one approved, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/move_pipeline.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 27 | `_event()` | Responsável por  event, conforme a implementação **[INFERÊNCIA]** |
| 41 | `_digest()` | Responsável por  digest, conforme a implementação **[INFERÊNCIA]** |
| 63 | `_verify_plan()` | Responsável por  verify plan, conforme a implementação **[INFERÊNCIA]** |
| 107 | `move_verified_test_file()` | Responsável por move verified test file, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/plan_memory.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 23 | `latest_recursive_plan()` | Retém apenas um resultado do planejador ligado ao snapshot da sessão. **[DOC]** |
| 44 | `blocked_details()` | Responsável por blocked details, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/planner.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 19 | `_contains_symlink()` | Rejeita links simbólicos em qualquer componente existente. **[DOC]** |
| 24 | `propose_moves()` | Responsável por propose moves, conforme a implementação **[INFERÊNCIA]** |
| 118 | `summarize_consolidation()` | Responsável por summarize consolidation, conforme a implementação **[INFERÊNCIA]** |
| 240 | `propose_date_moves()` | Responsável por propose date moves, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/preview.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 13 | `preview_inventory_page()` | Responsável por preview inventory page, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/queue_move.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 17 | `move_queue_approved()` | Responsável por move queue approved, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/recursive_plan.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 22 | `propose_recursive_consolidation()` | Responsável por propose recursive consolidation, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/table_rows.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 13 | `inventory_preview_rows()` | Responsável por inventory preview rows, conforme a implementação **[INFERÊNCIA]** |
| 20 | `origin_rows()` | Responsável por origin rows, conforme a implementação **[INFERÊNCIA]** |
| 28 | `duplicate_rows()` | Responsável por duplicate rows, conforme a implementação **[INFERÊNCIA]** |
| 39 | `date_plan_rows()` | Responsável por date plan rows, conforme a implementação **[INFERÊNCIA]** |
| 56 | `catalog_rows()` | Responsável por catalog rows, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/verified_copy.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 24 | `_journal()` | Registro JSONL exclusivo da cópia; nunca misturar com journal de move. **[DOC]** |
| 38 | `_fingerprint()` | Copia bytes para temporário aberto exclusivamente e verifica SHA-256. **[DOC]** |
| 79 | `_validate_plan()` | Responsável por  validate plan, conforme a implementação **[INFERÊNCIA]** |
| 126 | `copy_verified_test_file()` | Responsável por copy verified test file, conforme a implementação **[INFERÊNCIA]** |
| 212 | `inspect_verified_copy_test()` | Diagnóstico SOMENTE LEITURA de cópia em fixture. **[DOC]** |
| 293 | `_existing_regular()` | Responsável por  existing regular, conforme a implementação **[INFERÊNCIA]** |
| 307 | `digest()` | Responsável por digest, conforme a implementação **[INFERÊNCIA]** |
| 348 | `reconcile_published_test_copy()` | Responsável por reconcile published test copy, conforme a implementação **[INFERÊNCIA]** |
| 376 | `stable_digest()` | Responsável por stable digest, conforme a implementação **[INFERÊNCIA]** |

## `src/archivia/video_thumbnails.py`

| Linha | Função / método | Responsabilidade |
|---:|---|---|
| 33 | `VideoThumbnailService.__init__()` | Responsável por   init  , conforme a implementação **[INFERÊNCIA]** |
| 56 | `VideoThumbnailService.reset()` | Esquece pedidos antigos; interrompe a fonte sem descartar o cache. **[DOC]** |
| 68 | `VideoThumbnailService.request()` | Responsável por request, conforme a implementação **[INFERÊNCIA]** |
| 87 | `VideoThumbnailService._start_next()` | Responsável por  start next, conforme a implementação **[INFERÊNCIA]** |
| 113 | `VideoThumbnailService._media_status()` | Responsável por  media status, conforme a implementação **[INFERÊNCIA]** |
| 128 | `VideoThumbnailService._on_media_error()` | Responsável por  on media error, conforme a implementação **[INFERÊNCIA]** |
| 131 | `VideoThumbnailService._frame_ready()` | Responsável por  frame ready, conforme a implementação **[INFERÊNCIA]** |
| 167 | `VideoThumbnailService._finish()` | Responsável por  finish, conforme a implementação **[INFERÊNCIA]** |
| 184 | `VideoThumbnailService.close()` | Responsável por close, conforme a implementação **[INFERÊNCIA]** |

