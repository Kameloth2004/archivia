# Cenários de duplicatas SHA-256 — TEST-ONLY

Arquivos sintéticos de texto com extensão `.jpg`, **não são imagens reais**.
Esses fixtures não devem sair de `tests/` nem ser usados como mídias de produção.

- `A/foto_igual.jpg`, `B/foto_igual.jpg`, `B/alias_nome_diferente.jpg`: **mesmos bytes**, com nomes iguais e diferentes.
- `C/foto_igual.jpg`: **mesmo nome**, conteúdo diferente, mesmo tamanho.
- `A/mesmo_tamanho.jpg`, `B/mesmo_tamanho.jpg`: **mesmo nome e tamanho**, bytes diferentes.
- `A/vazio.jpg` e `B/vazio_copia.jpg`: ambos vazios (hash SHA-256 vazio idêntico).

O SHA-256 deve encontrar **dois grupos**: três arquivos com conteúdo igual e dois vazios;
os arquivos que apenas parecem repetidos por metadados não devem ser confirmados.

Para teste manual na GUI, primeiro faça prévia e catalogação explícita de
`tests/fixtures/sha256_demo` pela aba Inventário, em snapshot separado. Não substitui
snapshots anteriores. A verificação por SHA-256 nunca modifica esses fixtures.
