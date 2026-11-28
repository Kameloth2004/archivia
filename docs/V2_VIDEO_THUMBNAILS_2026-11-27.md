# ArchivIA V2 — Miniaturas de vídeos (fase 2)

Data: 27/11/2026. Branch derivada de `feat/v2-video-player-2026-11-27` (PR #8), por sua vez derivada da correção AVIF/JFIF do PR #7. A integração em `develop/v2.0.0` requer preservar essa ordem.

## Funcionalidade

- `video_thumbnails.VideoThumbnailService` opera serialmente no loop do Qt com `QMediaPlayer` e `QVideoSink`. Apenas um vídeo é decodificado de cada vez; a fonte permanece local e o áudio é silenciado.
- O serviço tenta extrair um quadro depois do carregamento (busca ~1 s quando seek é possível). Após um quadro válido, para a reprodução e libera a fonte. Se não houver quadro ou o backend falhar, vence o timeout de 1,8 s e o Explorador mantém o ícone genérico.
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

## Regressão Windows: WinError 32 no teste do visualizador (28/11/2026)

No relato de homologação: `Ran 360 tests in 73.694s — FAILED (errors=1, skipped=2)`; o erro ocorreu no `tearDown` de `test_old_async_image_is_ignored_after_navigating`, ao remover `segunda.png` ainda em leitura.

**Causa identificada:** o mock de `FilePreviewDialog._submit_image` abrangia somente a construção do diálogo, mas o teste navegava para uma segunda imagem **fora** do contexto de mock. Isso disparava leitura real de imagem na thread global enquanto a fixture era excluída. O teste `test_next_file_can_load_one_more_batch` apresentava o mesmo padrão.

**Correções:**
- Em ambos os testes, manter o mock durante a navegação e aguardar explicitamente `dialog._pool.waitForDone(10000)` antes de excluir as fixtures; não ignorar erros de limpeza.
- No visualizador de produção, usar `QThreadPool(self)` próprio com duas threads, em vez do pool global, isolando o ciclo de vida das leituras do diálogo.
- Não alterar `image_decode.py`, algoritmos de movimentação, hash, journal ou media player.

**Pendente:** executar no Windows testes do visualizador, miniaturas de vídeo e depois a suíte completa. Esta correção não prova ausência de todos os locks de arquivos em tarefas multimídia; verificar fechamento e troca rápida de arquivos também na homologação manual.

## Otimização de desempenho (28/11/2026)

O usuário observou aproximadamente **5 minutos** para gerar miniaturas numa pasta de **86 itens**. Causa provável: pipeline serial com até 5 segundos por vídeo e `setPosition(1000)` antes da captura, que pode exigir busca de keyframe e retardar a primeira imagem.

A otimização deste PR:
- elimina o seek obrigatório para 1 segundo e captura o **primeiro quadro válido**;
- reduz o timeout para **1.800 ms** por vídeo (revisável após benchmark);
- adiciona cache de tentativas malsucedidas para evitar reprocessamento do mesmo arquivo inalterado durante rolagens e redesenhos;
- permite nova tentativa após trocar/atualizar pasta, limpando o cache negativo no `reset()`;
- mantém a fila serial, cache positivo e separação do player em tela cheia;
- adiciona três testes de regressão para cache negativo, ausência de seek e descarte de geração.

**Limitação:** vídeos com decodificação lenta podem perder a miniatura nessa tentativa e exibir o ícone padrão. A redução de tempo é uma hipótese de melhoria, **não uma medição homologada**. Aguardar teste Windows na pasta real, verificando total de miniaturas, consumo e duração; se muitos vídeos não conseguirem gerar quadro, rever timeout ou implementar um extrator alternativo controlado. Nenhum vídeo original é modificado.
