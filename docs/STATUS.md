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
6. Testes em `tests/`; dados temporários em `tests/.runtime/`; mocks identificados como `MOCK-ONLY`.

## Validação confirmada pelo usuário

- 19 testes executados no Windows: `OK (skipped=1)` — 18 aprovados e um ignorado por restrição de links simbólicos.
- Planejador manual: uma ação proposta para `foto_teste.jpg`; zero bloqueios; nenhum arquivo movido.
- **Primeira integração Ollama real aprovada em 2026-11-21.** Pergunta: "Quantas imagens existem no meu catálogo?" Modelo: `qwen3:8b-q4_K_M`. O agente chamou `resumo_catalogo`, obteve `scan_id=1`, `media_files=1`, `by_category.imagem=1` e respondeu "O catálogo contém 1 imagem.". A saída indicou `files_modified=false`.
- Esse teste confirma chamada de ferramenta e consulta SQLite, **não** valida reconhecimento visual nem operações sobre arquivos.

## Próximo passo seguro

Testar, ainda com arquivos sintéticos, a solicitação de simulação via agente:
```bash
cd /d/PROJETOS/archivia
python -m archivia agente "Simule a organização das imagens catalogadas na pasta D:/PROJETOS/archivia/tests/fixtures/manual/destino. Não mova nada." --modelo "qwen3:8b-q4_K_M"
```
Verificar `tools_used[0].tool=simular_movimentacao`, `mode=simulation`, `executable=false`, `files_modified=false`, sem arquivos no destino.

## Limitações e evolução

- O agente não lê conteúdos visuais, apenas metadados do SQLite.
- O planejador ainda carrega itens da categoria em memória; implementar paginação antes de escalonar.
- Próximas etapas: mais validações das ferramentas, interface gráfica PySide6 e análise visual local.
- Nenhum modelo recebe comandos para mover, apagar ou executar shell; não há executor.

## Referências

- [Arquitetura](ARCHITECTURE.md)
- [Contrato do agente](AGENT.md)
- [Política de testes](../tests/README.md)
