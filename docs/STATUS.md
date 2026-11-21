# ArchivIA — Estado e retomada

Atualizado em 2026-11-21.

## Ambiente
- Windows, Git Bash, Python 3.12, projeto: `D:/PROJETOS/archivia`.
- Repositório: `Kameloth2004/archivia`, branch `main`.
- Ollama local e RTX 3060 12 GB; adaptador experimental implementado, ainda não validado com modelo real.

## Implementado
1. Inventário de imagens, vídeos e áudios por extensão e metadados.
2. Catálogo SQLite persistente em `data/catalogo.sqlite3`.
3. Consultas e resumo do último snapshot, sem revarrer as mídias.
4. Planejador **somente simulação** de movimentos por categoria, sem qualquer executor.
5. Adaptador experimental Ollama com allowlist de ferramentas (resumo e simulação), sem executor.\n6. Testes em `tests/`; execução temporária em `tests/.runtime/`.

## Validação
- No Windows, 7 testes passaram como `OK (skipped=1)` na etapa anterior.
- Posteriormente foram adicionados dois testes do resumo; **não há resultado relatado pelo usuário ainda** para estes nem para o novo planejador.
- Verificar execução de todos os testes após `git pull`.

## Próximo passo
1. Rodar `python -m unittest discover -s tests -v`.
2. Simular usando **somente diretórios de teste**, já catalogados e existentes.
3. Em etapa posterior, implementar consulta paginada para não carregar biblioteca grande em memória; considerar interface PySide6 e adaptador Ollama por chamada de ferramentas.

## Comandos
```bash
cd /d/PROJETOS/archivia
git pull origin main
python -m unittest discover -s tests -v
python -m archivia resumo
```

## Protocolo do agente\nConsultar [AGENT.md](AGENT.md).\n\n## Política de testes
`tests/README.md` é a referência. Marcas `TEST-ONLY` / `MOCK-ONLY` para componentes temporários. Nunca introduzir funções de teste no motor de produção.
