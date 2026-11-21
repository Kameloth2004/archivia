# ArchivIA

Bibliotecário digital local em Python, planejado para catalogar, classificar, renomear e organizar arquivos com apoio do Ollama.

## Estado do projeto

**Etapa experimental do agente Ollama: ferramentas de consulta e simulação sobre o motor Python.** A integração local com `qwen3:8b-q4_K_M` já foi validada. Nenhuma operação de renomeação, movimentação ou exclusão foi implementada.

### Princípios

- Python e biblioteca padrão nesta primeira etapa; nenhuma dependência de nuvem.
- Operações que alteram arquivos somente em etapas futuras, com prévia e aprovação.
- A varredura examina nomes e metadados dos arquivos, incluindo documentos, compactados e código; **não abre conteúdo nem arquivos ZIP**.
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

## Documentação para manutenção e retomada

- [Arquitetura e segurança](docs/ARCHITECTURE.md)
- [Categorias e inventário universal](docs/INVENTORY.md)
- [Agente Ollama: protocolo e limitações](docs/AGENT.md)
- [Edições planejadas: Standard e duas Lite](docs/EDITIONS.md)
- [Estado atual e próximos passos](docs/STATUS.md)
- [Interface gráfica Standard](docs/GUI.md)
- [Política de testes e mocks](tests/README.md)

## Primeira interface gráfica Standard

Instalação opcional no Windows: `python -m pip install -e ".[gui]"`. Abrir com `archivia-gui`. A janela inicial permite consultar resumo SQLite e conversar com o Ollama; não move arquivos. Consulte [GUI.md](docs/GUI.md).

## Catalogar pela GUI (confirmação necessária)

Após **Examinar pasta — prévia**, o botão **Salvar inventário no catálogo SQLite...** fica disponível se a leitura não tiver erros. Uma caixa de diálogo solicita confirmação; o motor reexamina a pasta e só grava um novo snapshot se o conteúdo listado e os metadados ainda coincidirem com a prévia. A gravação altera apenas o banco SQLite; nenhum arquivo da pasta é modificado. Um inventário antigo permanece disponível no histórico, embora a interface liste somente o último snapshot. Consulte [GUI.md](docs/GUI.md) e [INVENTORY.md](docs/INVENTORY.md).

## Agente Ollama local (experimental)

O agente utiliza apenas ferramentas autorizadas: `resumo_catalogo` e `simular_movimentacao`. Não pode mover, renomear ou apagar arquivos.

```bash
python -m archivia agente "Quantas imagens há no catálogo?" --modelo "qwen3:8b-q4_K_M"
```

É necessário que o Ollama local esteja ativo e que o nome do modelo corresponda ao retornado por `ollama list`. O suporte a tool calling varia por modelo. Primeiro execute os testes automatizados. Para detalhes e limites de segurança, leia [AGENT.md](docs/AGENT.md).

## Planejador em modo simulação

O comando `planejar` oferece apenas uma prévia, **sem mover ou alterar arquivos**. Ele lê o último snapshot SQLite e exige um diretório de destino existente. Para testes, utilize pastas dentro de `tests/fixtures/manual/`.

```bash
python -m archivia planejar --categoria imagem --destino "D:/PROJETOS/archivia/tests/fixtures/manual/destino"
```

A saída JSON é exibida no terminal, **não** é salva como arquivo. Operações são apenas propostas ou bloqueadas. Não existe executor. Um plano não é autorização para movimentar mídias. A operação inicial é limitada a 100 propostas; internamente ainda carrega a listagem da categoria em memória — consulte as limitações em `docs/ARCHITECTURE.md`.

## Resumo compacto do catálogo

O comando padrão para obter totais sem listar todas as mídias:

```bash
python -m archivia resumo
```

Usa consulta agregada no SQLite em modo somente leitura, recuperando somente o último snapshot. Exibe contagens por categoria, bytes e data da última catalogação. Não produz arquivo JSON no disco nem varre mídias. O resultado no terminal ainda é JSON pequeno, para permitir integração futura com interface gráfica.

## Histórico de inventários na GUI

Em **Biblioteca catalogada**, clique **Atualizar histórico** e selecione um snapshot anterior, por exemplo #1 (teste) ou #2 (`IW8 CONSTRUMAQ`). A listagem paginada consulta apenas aquele snapshot, sem varrer discos nem modificar o banco. O resumo superior e as ferramentas do agente continuam usando o snapshot mais recente nesta etapa. Consulte [GUI.md](docs/GUI.md).

## Consultar o catálogo

Depois de catalogar, consulte o último snapshot com um comando exclusivo de leitura:

```bash
python -m archivia consultar
python -m archivia consultar --categoria imagem
```

O comando `consultar` abre o SQLite em modo somente leitura (`mode=ro`), sem criar tabelas nem modificar dados. O filtro `--categoria` aceita `imagem`, `video` ou `audio`. Apenas o inventário mais recente é retornado; snapshots anteriores permanecem preservados no banco. Uma origem não é varrida novamente durante a consulta. Snapshots antigos permanecem com as categorias que estavam disponíveis quando foram gravados.

## Política de testes e mocks

Todos os testes automatizados, testes manuais, fixtures e mocks vivem em `tests/`. Os bancos e arquivos temporários usados por testes automatizados ficam em `tests/.runtime/` e são limpos após cada caso. A pasta antiga `teste-midias/` na raiz é legado de teste manual e **não deve ser apagada automaticamente**. Para futuros testes manuais, use `tests/fixtures/manual/`.

Detalhes: [tests/README.md](tests/README.md). Marcadores `TEST-ONLY` e `MOCK-ONLY` indicam componentes de teste; código de produção não deve importar esses componentes.

## Catálogo SQLite local

Após atualizar o código (`git pull`), execute na raiz do projeto:

```bash
python -m archivia catalogar "D:/PROJETOS/archivia/tests/fixtures/manual"
```

O arquivo será criado automaticamente em `D:/PROJETOS/archivia/data/catalogo.sqlite3`. O caminho pode ser alterado com `--banco`, caso necessário. A pasta `data/` é ignorada pelo Git: **não publique o banco**, pois contém caminhos e nomes dos arquivos.

Cada execução grava um novo snapshot identificado por `scan_id`; não remove registros de inventários anteriores. Se houver erros na varredura, nenhum snapshot é gravado. O catálogo guarda apenas metadados, e **não renomeia, altera, abre ou movimenta as mídias**. É necessário ter permissão de escrita apenas na pasta do banco. A integração Ollama está disponível somente nos comandos de agente autorizados; o inventário e catálogo não dependem dela.

### Saída

Um objeto JSON em UTF-8, contendo `root`, `files`, `summary` e `errors`. A lista inclui todos os arquivos regulares: imagem, vídeo, áudio, documento, planilha, apresentação, compactado, código e outros. Tipos desconhecidos entram como `outro`. Arquivos e diretórios simbólicos são ignorados. Arquivos ocultos não são excluídos automaticamente.

Os metadados incluem caminho relativo, categoria baseada **somente na extensão**, extensão, tamanho em bytes e instante de modificação (UTC). Essa categorização inicial não é classificação semântica.

### Limitações desta etapa

- Inventários grandes são mantidos na memória antes de imprimir o JSON.
- O inventário pode mudar durante uma varredura; não é um snapshot atômico.
- Permissões do sistema operacional são respeitadas: leia somente diretórios de sua confiança.
- Nenhuma identificação de duplicatas por hash ou reconhecimento visual ainda; a conexão Ollama com ferramentas de consulta e simulação já foi testada.

## Próximas etapas planejadas

1. Consultas e filtros do último snapshot SQLite (implementados).
2. Detecção de duplicatas e leitura controlada de metadados especializados.
3. Adaptador local Ollama para categorização semântica.
4. Plano de mudanças em modo simulação, com aprovação explícita e trilha de auditoria.
5. Organização efetiva, com medidas de recuperação e proteção contra conflitos.
