# ArchivIA V2 — Reprodutor local de vídeo (fase 1)

Data: 27/11/2026.

## Base e integração

Esta branch foi derivada de `fix/v2-avif-preview-decoder-2026-11-27` (PR #7). Os recursos AVIF/JFIF e imagens da V2 foram mantidos. O PR de vídeo deve ser revisado **contra essa branch**, e só depois de integrar o PR #7 em `develop/v2.0.0` deve ser retomada a integração de vídeo. Nunca sobrescrever o visualizador de imagens da V2 com uma versão antiga.

## Recursos implementados

- `src/archivia/gui_video.py`: `LocalVideoPlayer` com `QMediaPlayer`, `QVideoWidget`, `QAudioOutput`.
- Play, Pause, Parar, voltar/avançar 10 segundos (somente se mídia permitir seek), volume e mute.
- Linha do tempo com duração e posição; arrastar para procurar trecho reproduzível.
- `FilePreviewDialog` passa a mostrar o player ao abrir vídeo, depois de validar escopo e dados stat com `verified_file`.
- **Sem autoplay**; o arquivo somente é carregado, e a reprodução depende de clique no Play.
- Navegar para outro arquivo ou fechar chama `release`: para a reprodução e limpa a fonte para soltar o handle.
- Propriedades e metadados sob comando explícito permanecem existentes.
- Nenhum vídeo é alterado, movido, excluído, transcodificado ou enviado para a rede.

## Limites e compatibilidade

Formatos candidatáveis pelo sufixo: mp4, m4v, mov, mkv, avi, webm, wmv, flv, mpeg, mpg, 3gp. **A existência do sufixo não garante codec suportado**: o backend Qt Multimedia / FFmpeg e o pacote efetivamente instalado determinam a reprodução. Mensagens de erro do backend são exibidas ao usuário.

Por enquanto **as miniaturas dos vídeos continuam genéricas**. A extração controlada dos quadros será feita em uma segunda etapa, com fila, cache e descarte de tarefas durante navegação; não antecipar isso como concluído.

## Testes

`tests/test_gui_video_v2.py` acrescenta cenários de formato do tempo, estado inicial, ausência de autoplay, liberação de fonte, seek e navegação para imagem. Usa fixture fictícia, portanto **não valida codecs de vídeo reais**.

**Pendente executar testes no Windows**. A suíte completa deve permanecer aprovada; também validar manualmente MP4 H.264/AAC com arquivo descartável antes de integrar.

### Comandos de homologação

```bash
git fetch origin feat/v2-video-player-2026-11-27
git switch -c feat/v2-video-player-2026-11-27 FETCH_HEAD
python -m unittest discover -s tests -p "test_gui_video_v2.py" -v
python -m unittest discover -s tests -v
```

Se branch já existir localmente, não recriar; usar `git merge --ff-only FETCH_HEAD` após mudar para ela.

## Próxima etapa

Miniaturas reais de vídeo em segundo plano, geração de quadro com `QVideoSink` ou backend adequado, com validação de arquivos e cache limitado; nenhum autoplay oculto e nenhuma escrita em arquivo do acervo.
