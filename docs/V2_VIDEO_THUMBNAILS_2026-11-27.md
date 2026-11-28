# ArchivIA V2 — Miniaturas de vídeos (fase 2)

Data: 27/11/2026. Branch derivada de `feat/v2-video-player-2026-11-27` (PR #8), por sua vez derivada da correção AVIF/JFIF do PR #7. A integração em `develop/v2.0.0` requer preservar essa ordem.

## Funcionalidade

- `video_thumbnails.VideoThumbnailService` opera serialmente no loop do Qt com `QMediaPlayer` e `QVideoSink`. Apenas um vídeo é decodificado de cada vez; a fonte permanece local e o áudio é silenciado.
- O serviço tenta extrair um quadro depois do carregamento (busca ~1 s quando seek é possível). Após um quadro válido, para a reprodução e libera a fonte. Se não houver quadro ou o backend falhar, vence o timeout de 5 s e o Explorador mantém o ícone genérico.
- Fila limitada a 24 pedidos e cache LRU limitado a 128 quadros **somente em RAM**. A chave inclui caminho, tamanho e `mtime_ns`; tarefas de gerações antigas são descartadas após troca de pasta.
- `gui_explorer.ExplorerPanel` solicita miniaturas apenas para itens visíveis e próximos, como já faz com imagens; aplica um símbolo Play sobre a prévia. A criação de `QPixmap` e de `QIcon` ocorre na thread da GUI.
- Não grava miniaturas no acervo, não modifica vídeos, não transmite dados e não libera execução ao agente Ollama.
- O reprodutor de tela cheia da primeira etapa permanece independente: seu Play continua sendo uma ação explícita do usuário. O processo transitório de extração de quadros **não é autoplay na interface**, mas precisa decodificar o vídeo internamente.
- Extensões: seguem `gui_video.VIDEO_EXTENSIONS`. Suporte efetivo depende de codecs Qt Multimedia disponíveis no Windows.

## Arquivos

- Novo: `src/archivia/video_thumbnails.py`
- Atualizado: `src/archivia/gui_explorer.py`
- Novo: `tests/test_video_thumbnails_v2.py` (cinco testes de fila, cache, descarte e integração sem decodificar vídeo real)

## Limitações e riscos

- Não há persistência do cache em disco: voltar à pasta na mesma sessão pode reaproveitar imagens; reiniciar a aplicação gera miniaturas sob demanda novamente.
- Como toda decodificação depende dos codecs locais, vídeos não suportados conservarão o ícone padrão.
- A fila usa recursos assíncronos do Qt Multimedia e ainda deve ser testada com vídeos reais em diferentes formatos, incluindo navegação rápida, fechamento durante a extração e arquivos com codecs inválidos.
- Em arquivos enormes, a carga de decodificação do primeiro quadro depende do backend. A fila serial e timeout mitigam, mas não substituem limites internos de memória do decodificador.
- Não foi executado teste de compatibilidade do Windows pelo assistente.

## Homologação sugerida

```bash
git fetch origin feat/v2-video-thumbnails-2026-11-27
git switch -c feat/v2-video-thumbnails-2026-11-27 FETCH_HEAD
python -m unittest discover -s tests -p "test_video_thumbnails_v2.py" -v
python -m unittest discover -s tests -v
```

Depois abrir o ArchivIA na pasta de vídeos, verificar miniaturas reais MP4, Play sobre quadro e que a interface continua responsiva; navegar rapidamente para outra pasta e fechar durante a geração; testar visualização de imagens e reprodução de vídeos existentes.

Somente após a homologação, integrar PR #7, depois PR #8, e finalmente este PR; evitar merge de branches aninhadas fora de ordem.
