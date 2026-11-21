# ArchivIA — Estado e retomada

Atualizado em 2026-11-21.

## Ambiente

- Windows, Git Bash, Python 3.12, projeto: `D:/PROJETOS/archivia`.
- Repositório: `Kameloth2004/archivia`, branch `main`.
- Ollama local, RTX 3060 12 GB.
- Modelo utilizado no primeiro teste real: `qwen3:8b-q4_K_M`.

## Implementado

1. Inventário de imagens, vídeos e áudios por extensão e metadados.
2. Catálogo SQLite persistente em `data/catalogo.sqlite3`.
3. Consultas e resumo do último snapshot, sem revarrer mídias.
4. Planejador de movimentos **exclusivamente em simulação**, sem executor.
5. Adaptador local Ollama com allowlist de ferramentas: `resumo_catalogo` e `simular_movimentacao`.
6. Interface gráfica PySide6 inicial criada em `src/archivia/gui.py`; instalação opcional concluída e janela aberta no Windows em 2026-11-21.
7. Seletor de pastas, prévia de inventário e tabela paginada adicionados à GUI. **Tabela catalogada validada no Windows por captura de tela:** `foto_teste.jpg`, categoria `imagem`, extensão `.jpg`, 15 bytes; página 1 de 1. Seletor nativo e prévia **validados no Windows por captura de tela**: pasta `D:/PROJETOS/archivia/tests/fixtures/manual`, 1 mídia, 1 imagem, 0 vídeos, 0 áudios e 0 erros.
8. Testes em `tests/`; dados temporários em `tests/.runtime/`; mocks identificados como `MOCK-ONLY`.

## Validação confirmada pelo usuário

- 19 testes executados no Windows: `OK (skipped=1)` — 18 aprovados e um ignorado por restrição de links simbólicos.
- Planejador manual: uma ação proposta para `foto_teste.jpg`; zero bloqueios; nenhum arquivo movido.
- **Primeira integração Ollama real aprovada em 2026-11-21.** Pergunta: "Quantas imagens existem no meu catálogo?" Modelo: `qwen3:8b-q4_K_M`. O agente chamou `resumo_catalogo`, obteve `scan_id=1`, `media_files=1`, `by_category.imagem=1` e respondeu "O catálogo contém 1 imagem.". A saída indicou `files_modified=false`.
- **Segunda integração real aprovada em 2026-11-21.** O Qwen3 chamou `simular_movimentacao`, categoria `imagem`, destino `tests/fixtures/manual/destino`, obteve `selected=1`, `blocked=0`, `mode=simulation`, `executable=false`, `files_modified=false`. Nenhum arquivo foi movido.
- Os testes comprovam integração por ferramentas, **não** reconhecimento visual, mecanismo de aprovação ou operações sobre arquivos.

**GUI: agente validado em 2026-11-21.** A pergunta pela interface retornou `O catálogo contém 1 imagem.`, com `tools_used` incluindo `resumo_catalogo`, `scan_id=1`, `imagem=1`, `files_modified=false`. Essa evidência comprova a rota GUI → Ollama → Python → SQLite → GUI.

**GUI: simulação validada em 2026-11-21.** Pela janela PySide6 o Qwen3 chamou `simular_movimentacao`, com `scan_id=1`, `foto_teste.jpg`, `selected=1`, `blocked=0`, `mode=simulation`, `executable=false`; nenhum arquivo foi movimentado. A resposta do modelo sugeriu aprovação, mas tal funcionalidade **não existe** ainda — corrigir orientação/UX para não induzir o usuário a acreditar que há executor.

## GUI Standard

Protótipo inicial: `archivia-gui`, instalado opcionalmente com `python -m pip install -e ".[gui]"`. **Usuário confirmou que dependências instalaram e a janela abriu normalmente em 2026-11-21**, com captura de tela. O botão **Atualizar resumo** foi testado e aprovado pelo usuário; a interação com o agente pela GUI foi aprovada: `resumo_catalogo` devolveu 1 imagem via Qwen3. A interface atual é explicitamente provisória: redesenhar futuramente para aparência moderna, melhor hierarquia visual, navegação intuitiva e fluxos claros. Ver [GUI.md](GUI.md).

## Atualização — tabela de prévia de inventário

- Novo `src/archivia/preview.py`: fatia dados do inventário em memória, filtra por categoria, sem SQLite nem modificação de mídia.
- GUI: adicionada tabela própria para o inventário recém-examinado, com 50 registros por página, filtro de imagens/vídeos/áudios e navegação Anterior/Próxima, independente da biblioteca catalogada.
- O inventário completo permanece em memória durante a sessão; trocar a pasta ou executar nova varredura substitui a prévia anterior. Para 19.636 arquivos, a tela cria apenas 50 linhas por vez. Ainda será necessário medir uso de RAM em bibliotecas maiores.
- Corrigido erro visual antigo no painel do agente após prévia bem-sucedida.
- Novos testes isolados em `tests/test_preview.py`. **Ainda não validados no Windows**; requer `git pull` e suíte completa.
- Não há gravação SQLite nem movimentação de arquivos neste fluxo.

## Próximo passo seguro

**Próxima validação:** executar suíte completa e testar a tabela de prévia na pasta `D:/IW8 CONSTRUMAQ` (último teste: 19.636 mídias, 19.511 imagens, 125 vídeos, 0 erros), verificando navegação e filtro sem catalogar. Não habilitar execução real.

## Limitações e evolução

- O agente não lê conteúdos visuais, apenas metadados do SQLite.
- A GUI já usa consultas SQL paginadas; o planejador e o comando `consultar` ainda carregam itens da categoria em memória. Planejador deverá migrar para paginação antes de escalonar.
- Próximas etapas: interface gráfica PySide6, paginação SQLite e análise visual local.
- **Três edições planejadas, sem implementação separada no momento:** Standard (prioritária), Lite sem IA e Lite + IA opcional. Consultar [EDITIONS.md](EDITIONS.md).
- Nenhum modelo recebe comandos para mover, apagar ou executar shell; não há executor.

## Referências

- [Arquitetura](ARCHITECTURE.md)
- [Contrato do agente](AGENT.md)
- [Edições e prioridades](EDITIONS.md)
- [Política de testes](../tests/README.md)
