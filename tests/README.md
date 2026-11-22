# Política de testes — ArchivIA

**Regra de ouro:** testes, fixtures, mocks e dados gerados exclusivamente para testes devem ficar sob `tests/`. O código de produção fica em `src/archivia/` e **não pode importar helpers de `tests/`**.

## Estrutura e identificação

- `test_*.py`: testes automatizados, permanentes enquanto houver funcionalidade coberta.
- `support.py`: auxiliares identificados como `TEST-ONLY`; não usados em produção.
- `fixtures/`: entradas sintéticas e exemplos manuais; **nunca** mídias pessoais reais.
- `fixtures/manual/`: arquivos criados para testes manuais (ignorado pelo Git).
- `.runtime/`: bancos SQLite, arquivos de teste e diretórios temporários dos testes automatizados (ignorado pelo Git, com limpeza por contexto).
- `mocks/`: reservado a mocks identificados como `MOCK-ONLY`, caso sejam necessários no futuro; todo mock deverá documentar qual dependência substitui.

## Cenário persistente para hash

`tests/fixtures/sha256_demo/` contém dados pequenos de teste identificados como **TEST-ONLY**, incluindo arquivos com extensão `.jpg` cujo conteúdo é texto sintético. Casos: arquivo idêntico em pastas distintas, nome diferente com bytes iguais, nome/tamanho iguais com bytes diferentes e dois arquivos vazios. O teste copia esses arquivos para `tests/.runtime/` antes de inventariar. Não executar tratamentos visuais sobre esses falsos JPEGs. Para testar manualmente a GUI, a pasta pode ser explicitamente catalogada como **novo snapshot de teste**; nunca substituir dados reais.

## Regras de manutenção e limpeza

1. Nunca colocar fixtures, mocks nem rotinas de teste em `src/archivia/`.
2. Marcar dados sintéticos, mocks e auxiliares com `TEST-ONLY` ou `MOCK-ONLY` em comentários/docstrings.
3. Criar bancos e arquivos de testes automatizados via `temporary_test_directory()`, sempre sob `tests/.runtime/`.
4. Não versionar saída gerada, bancos SQLite, dados privados ou pastas de execução.
5. Ao concluir uma fase, revisar mocks temporários e fixtures obsoletas; remover apenas o que não for mais utilizado, mantendo testes de regressão úteis.
6. Não apagar automaticamente dados de usuários. Antes de qualquer limpeza manual fora de `tests/.runtime/`, conferir caminhos e conteúdo.
7. A instalação e o código de produção não devem depender da presença da pasta `tests/`.

Execute na raiz do projeto:

```bash
python -m unittest discover -s tests -v
```

Observação: arquivos com extensões de mídia usados nos testes podem conter texto simulado. Isso valida o inventário por extensão; **não** prova decodificação ou análise visual/sonora.
