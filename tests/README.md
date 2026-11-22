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

## Cenário multipágina de SHA-256 — geração manual TEST-ONLY

O gerador `tests/generate_sha256_paged_demo.py` cria **134 arquivos sintéticos** exclusivamente sob `tests/`, sem versionar os arquivos gerados. Caminho padrão: `tests/fixtures/manual/sha256_paginado/` (ignorado pelo Git). O gerador **recusa destinos fora de `tests/`, links/junctions e pastas não vazias**; não apaga nem substitui arquivos existentes.

Na raiz do repositório:

```bash
python tests/generate_sha256_paged_demo.py
```

Arquivos `.jpg` contêm bytes sintéticos, não fotografias verdadeiras. Há três grupos de hashes iguais: `A/000_foto_original.jpg` + `L/050_alias_nome.jpg` + `Z/999_foto_copia.jpg`; `B/010_relatorio.jpg` + `Y/990_outro_nome.jpg`; e `C/020_vazio.jpg` + `X/980_vazio_copia.jpg`. Outros 125 arquivos têm tamanho semelhante mas conteúdo diferente; `D/030_mesmo_nome.jpg` e `W/970_mesmo_nome.jpg` têm mesmo nome-base e tamanho, mas conteúdos diferentes. Esperados **3 grupos, 7 arquivos idênticos, 134 analisados, 2 páginas SQL** com limite de 200.

A pasta `tests/fixtures/manual/` já é ignorada pelo Git; o gerador recusa repetir a criação sobre pasta preenchida. Os testes automatizados de `tests/test_sha256_paged_fixture.py` usam `tests/.runtime/`, sem criar esta pasta persistente.

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
