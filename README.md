# ArchivIA

Bibliotecário digital local em Python, planejado para catalogar, classificar, renomear e organizar mídias com apoio do Ollama.

## Estado do projeto

**Etapa 2: inventário somente leitura das mídias e persistência local no SQLite.** O Ollama ainda não é utilizado. Nenhuma operação de renomeação, movimentação ou exclusão foi implementada.

### Princípios

- Python e biblioteca padrão nesta primeira etapa; nenhuma dependência de nuvem.
- Operações que alteram arquivos somente em etapas futuras, com prévia e aprovação.
- A varredura examina nomes e metadados do sistema de arquivos; **não abre o conteúdo** das mídias.
- Links simbólicos não são percorridos; falhas de acesso são reportadas, não escondidas.
- O inventário é emitido no terminal; o comando separado `catalogar` grava somente no SQLite local.

## Executar

Requer Python 3.10 ou superior. Na raiz do repositório:

```bash
python -m pip install -e .
python -m archivia inventario "D:\\Minhas Midias"
```

Alternativamente, sem instalação, caso a pasta `src` esteja no `PYTHONPATH`:

```bash
PYTHONPATH=src python -m archivia inventario "/caminho/das/midias"
```

Para instalar em modo de desenvolvimento:

```bash
python -m pip install -e .
archivia inventario "/caminho/das/midias"
```

Para executar os testes:

```bash
python -m unittest discover -s tests -v
```

## Resumo compacto do catálogo

O comando padrão para obter totais sem listar todas as mídias:

```bash
python -m archivia resumo
```

Usa consulta agregada no SQLite em modo somente leitura, recuperando somente o último snapshot. Exibe contagens por categoria, bytes e data da última catalogação. Não produz arquivo JSON no disco nem varre mídias. O resultado no terminal ainda é JSON pequeno, para permitir integração futura com interface gráfica.

## Consultar o catálogo

Depois de catalogar, consulte o último snapshot com um comando exclusivo de leitura:

```bash
python -m archivia consultar
python -m archivia consultar --categoria imagem
```

O comando `consultar` abre o SQLite em modo somente leitura (`mode=ro`), sem criar tabelas nem modificar dados. O filtro `--categoria` aceita `imagem`, `video` ou `audio`. Apenas o inventário mais recente é retornado; snapshots anteriores permanecem preservados no banco. Uma origem não é varrida novamente durante a consulta.

## Política de testes e mocks

Todos os testes automatizados, testes manuais, fixtures e mocks vivem em `tests/`. Os bancos e arquivos temporários usados por testes automatizados ficam em `tests/.runtime/` e são limpos após cada caso. A pasta antiga `teste-midias/` na raiz é legado de teste manual e **não deve ser apagada automaticamente**. Para futuros testes manuais, use `tests/fixtures/manual/`.

Detalhes: [tests/README.md](tests/README.md). Marcadores `TEST-ONLY` e `MOCK-ONLY` indicam componentes de teste; código de produção não deve importar esses componentes.

## Catálogo SQLite local

Após atualizar o código (`git pull`), execute na raiz do projeto:

```bash
python -m archivia catalogar "D:/PROJETOS/archivia/tests/fixtures/manual"
```

O arquivo será criado automaticamente em `D:/PROJETOS/archivia/data/catalogo.sqlite3`. O caminho pode ser alterado com `--banco`, caso necessário. A pasta `data/` é ignorada pelo Git: **não publique o banco**, pois contém caminhos e nomes dos arquivos.

Cada execução grava um novo snapshot identificado por `scan_id`; não remove registros de inventários anteriores. Se houver erros na varredura, nenhum snapshot é gravado. O catálogo guarda apenas metadados, e **não renomeia, altera, abre ou movimenta as mídias**. É necessário ter permissão de escrita apenas na pasta do banco. Não há integração com Ollama nesta etapa.

### Saída

Um objeto JSON em UTF-8, contendo `root`, `files`, `summary` e `errors`. A lista inclui apenas extensões de mídias conhecidas (imagem, vídeo e áudio). Tipos não reconhecidos são contabilizados, mas não listados. Arquivos e diretórios simbólicos são ignorados. Arquivos ocultos não são excluídos automaticamente.

Os metadados incluem caminho relativo, categoria baseada **somente na extensão**, extensão, tamanho em bytes e instante de modificação (UTC). Essa categorização inicial não é classificação semântica.

### Limitações desta etapa

- Inventários grandes são mantidos na memória antes de imprimir o JSON.
- O inventário pode mudar durante uma varredura; não é um snapshot atômico.
- Permissões do sistema operacional são respeitadas: leia somente diretórios de sua confiança.
- Nenhuma identificação de duplicatas por hash, reconhecimento visual ou integração com Ollama ainda.

## Próximas etapas planejadas

1. Consultas e filtros do último snapshot SQLite (implementados).
2. Detecção de duplicatas e leitura controlada de metadados especializados.
3. Adaptador local Ollama para categorização semântica.
4. Plano de mudanças em modo simulação, com aprovação explícita e trilha de auditoria.
5. Organização efetiva, com medidas de recuperação e proteção contra conflitos.
