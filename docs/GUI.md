# ArchivIA Standard — Primeira interface gráfica (PySide6)

Estado: **protótipo inicial para homologação**, não é instalador, produto final nem interface de movimentação.

## Objetivo

Oferecer uma janela desktop para acessar o **mesmo motor Python** já validado pelo terminal, sem reimplementar SQLite nem agente Ollama.

## Instalação no ambiente Windows de desenvolvimento

No Git Bash, no projeto:

```bash
cd /d/PROJETOS/archivia
git pull origin main
python -m pip install -e ".[gui]"
python -m unittest discover -s tests -v
archivia-gui
```

PySide6 é **dependência opcional**: a instalação base `python -m pip install -e .` não baixa Qt. Os comandos `python -m archivia ...` seguem disponíveis sem PySide6.

## Categorias universais — atualização aguardando homologação

Filtros da prévia e da biblioteca SQLite expandidos: Imagens, Vídeos, Áudios, Documentos, Planilhas, Apresentações, Compactados, Código-fonte, Outros. O resumo mostra **Arquivos** (todos os tipos) e **Mídias** (somente imagem/vídeo/áudio). A lista de catálogo só exibirá tipos novos depois que um snapshot novo for gravado; por enquanto a GUI não tem botão de catalogação. Nenhum ZIP é aberto. Consulte [INVENTORY.md](INVENTORY.md).

## Terceira etapa visual — prévia detalhada do inventário

**Código implementado, aguardando homologação no Windows.** A área **Examinar pasta — prévia** passa a ter sua própria tabela paginada (50 itens), filtro por categoria e navegação independente do catálogo SQLite. Os dados vêm do inventário em RAM, sem escrita em SQLite ou manipulação de arquivos. Uma nova varredura substitui a prévia anterior; seleção de pasta limpa a prévia. A tabela da Biblioteca catalogada continua mostrando somente o último snapshot persistido.

O teste anterior com `D:/IW8 CONSTRUMAQ` encontrou 19.636 mídias (19.511 imagens, 125 vídeos, 0 erros), mas só mostrava totais. Esta etapa permitirá listar individualmente esses arquivos sem catalogação.

**Nota de desempenho:** a tabela renderiza 50 linhas por vez, porém `inventory()` ainda guarda todos os metadados na memória; streaming ou inventário incremental são evoluções futuras.

A mensagem de erro antiga no painel do agente passa a ser limpa quando a prévia termina com sucesso. Não foram adicionados botões para gravar snapshots nem mover arquivos.

## Segunda etapa visual — navegação e biblioteca

Implementado em código. **Tabela do catálogo homologada no Windows por captura de tela em 2026-11-21**; seletor de pasta e prévia **validados no Windows em 2026-11-21**:

- **Escolher pasta...** usa o seletor nativo do sistema operacional.
- **Examinar pasta — prévia** executa inventário de metadados somente leitura; **não cria snapshot SQLite** e não mostra os arquivos individuais da pasta escolhida.
- **Biblioteca catalogada** mostra a última catalogação SQLite em uma tabela com nome relativo, categoria, extensão e tamanho; filtro por categoria e botões Anterior/Próxima.
- A listagem utiliza `query_catalog_page()` no motor, com `LIMIT/OFFSET` SQL e 50 arquivos por página, evitando carregar a biblioteca completa na interface.
- A pasta escolhida para **Examinar** não substitui a origem do último catálogo; inventário e catálogo são ações separadas.
- Não há botão de catalogação nem alteração de mídias nesta etapa.

**Resultado do teste de tabela:** `foto_teste.jpg`, imagem, `.jpg`, 15 bytes, página 1 de 1; aprovado. O texto `Erro: Selecione uma pasta antes de examinar.` aparece corretamente se o usuário tentar executar a prévia com o campo de pasta vazio. **Teste aprovado:** pasta `D:/PROJETOS/archivia/tests/fixtures/manual`, 1 mídia/imagem, 0 erros, sem movimentação. O campo de origem e a tabela do catálogo permaneceram independentes.

**Ajuste de UX pendente:** o painel de resposta do agente preservou a mensagem de erro antiga `Selecione uma pasta antes de examinar` mesmo após a prévia ter funcionado. Evitar apresentação de erros obsoletos por meio de limpeza ou estados de erro separados por seção.

## Interface incluída nesta etapa

- Campo com caminho do SQLite; padrão `D:/PROJETOS/archivia/data/catalogo.sqlite3` no ambiente conhecido.
- Botão **Atualizar resumo**: consulta agregada do último snapshot, em modo somente leitura.
- Campo de modelo Ollama, padrão `qwen3:8b-q4_K_M`.
- Campo de pergunta e botão **Perguntar ao agente**.
- Painel para resposta e JSON das ferramentas realmente chamadas.
- Indicador de status/erros.
- Worker em thread separada para que a janela continue responsiva durante consultas lentas.

Observação de UX: o Qwen3 pode sugerir que o usuário aprove uma movimentação; **não existe atualmente recurso de aprovação nem executor**, de modo que tal sugestão é apenas texto do modelo. Ajustar o agente para deixar isso claro.

## Limites explícitos

- Não há operação de movimentação, renomeação ou exclusão. Pedidos para organizar somente geram **simulação** pelo agente.
- Já existe seletor de pastas e **prévia** do inventário, mas ainda não há botão para catalogar a pasta escolhida, miniaturas, análise visual, detecção de duplicatas ou organização real.
- O botão de resumo usa sempre o **último snapshot global** do banco, não a soma consolidada de múltiplas origens.
- A conversa não mantém histórico entre perguntas; uma pergunta gera uma solicitação independente.
- A interface não autentica nem gerencia instâncias Ollama; pressupõe serviço local disponível em `127.0.0.1:11434`.
- Instalação opcional PySide6 e abertura de `archivia-gui` **confirmadas no Windows em 2026-11-21** com captura de tela; botão **Atualizar resumo** e pergunta ao agente Ollama validados pelo usuário. Resposta recebida: `O catálogo contém 1 imagem.`, ferramenta `resumo_catalogo`, `files_modified=false`.
- Fechar a janela durante uma chamada ao Ollama é bloqueado até ela terminar para não interromper threads.

## Regras de arquitetura

- Código de interface em `src/archivia/gui.py` e nunca importado pelo motor/CLI.
- `agent.py`, `catalog.py` e `planner.py` permanecem independentes do Qt.
- Nenhuma dependência de GUI ou Ollama é obrigatória para o inventário básico.
- Testes, fixtures e mocks exclusivamente em `tests/`.
- Futuras edições Lite reutilizarão a mesma camada de negócio.

## Próxima validação

1. Rodar testes existentes após instalação opcional.
2. Abertura de `archivia-gui` e clique em **Atualizar resumo** **confirmados pelo usuário**.
3. Pergunta **Quantas imagens existem no meu catálogo?** pela GUI **aprovada**, com chamada `resumo_catalogo` e resultado de 1 imagem.
4. Se ocorrer erro, anotar traceback/saída e corrigir antes de adicionar novas funções.
5. **Aprovado em 2026-11-21:** simulação pela GUI com destino `D:/PROJETOS/archivia/tests/fixtures/manual/destino`: 1 arquivo proposto, 0 bloqueios, nenhum arquivo movido.
6. Seletor visual e prévia de inventário **aprovados**. Próxima evolução: exibir os itens examinados e oferecer catalogação com confirmação, mantendo leitura/simulação até aprovação explícita.

## Decisão de UX registrada em 2026-11-21

O usuário aprovou a abertura da GUI como marco técnico, **mas pediu explicitamente uma reformulação visual posterior**. A janela atual é apenas bancada funcional de homologação. Planejar interface mais bonita, moderna e intuitiva, com navegação clara, organização de painéis, seleção visual de diretórios, estados de carregamento, mensagens compreensíveis, miniaturas e prévia de operações. Não priorizar polimento visual antes da validação do motor e do fluxo agente-ferramentas; não esquecer esta exigência ao avançar o produto.

## Nova etapa: salvar prévia no catálogo SQLite (aguardando validação)

- Botão **Salvar inventário no catálogo SQLite...**, inicialmente desabilitado; habilita somente após varredura concluída sem erros.
- Ao clicar, mostra janela de confirmação explícita com origem, total de arquivos e caminho do banco.
- Se confirmar, o worker reexamina a pasta e compara lista completa, categoria, tamanho, mtime e resumo da nova leitura com a prévia. **Se algo mudou, recusa gravar**.
- Se forem idênticos, cria **novo snapshot** no banco SQLite por `store_inventory()`; arquivos originais permanecem intocados.
- Não permite gravar duas vezes sem nova prévia; mudança de pasta invalida a prévia.
- A interface limpa a tabela do catálogo anterior após salvar e pede nova consulta, para não misturar snapshots.
- O botão não é uma autorização de movimentação; **somente o SQLite pode ser escrito**. Não existe executor.
- Limite técnico: comparação e inventário em RAM e verificação não atômica em relação a alterações simultâneas. Ainda não é inventário transacional do sistema de arquivos.
- **Não testar inicialmente em `D:/IW8 CONSTRUMAQ`**: primeiro validar com `D:/PROJETOS/archivia/tests/fixtures/manual` e banco `data/catalogo.sqlite3`. A operação pode gravar um novo snapshot no banco de desenvolvimento, sem excluir o antigo.
- Testes automatizados em `tests/test_cataloging.py`, sem dependência de Qt nem dados pessoais.

## Histórico de snapshots — nova etapa (pendente de homologação)

- A **Biblioteca catalogada** agora possui uma caixa **Histórico de snapshots** e botão **Atualizar histórico**.
- O histórico consulta exclusivamente o SQLite, retornando até os 100 snapshots mais recentes com ID, data, origem e quantidade de arquivos, sem varrer pastas.
- O padrão **Mais recente (automático)** preserva o comportamento anterior. Selecionar um ID específico filtra a tabela catalogada para aquele inventário histórico (50 linhas por página, filtros por categoria).
- A área superior de **Atualizar resumo** continua mostrando o inventário globalmente mais recente, independentemente da seleção no histórico. A distinção será aprimorada na reformulação visual.
- O agente Ollama e seu planejador ainda utilizam o snapshot mais recente, não o histórico selecionado na GUI; essa restrição evita ambiguidade nesta fase.
- Testar no Windows selecionando **#1**, com `foto_teste.jpg`, e **#2**, com os 44.383 arquivos de `D:/IW8 CONSTRUMAQ`.
- Nunca altera o banco, os arquivos originais ou os snapshots antigos.
- Testes de regressão em `tests/test_catalog.py`, dentro da estrutura de testes.

## Origens catalogadas — atualização para homologação

Além do histórico, o painel **Origens catalogadas — último snapshot por pasta** apresenta uma linha para cada caminho de origem distinto, com ID do snapshot mais novo, quantidade de arquivos e mídias. Clique em **Atualizar origens** para obter os valores diretamente do SQLite. O painel soma somente os snapshots mais novos de cada pasta, não o histórico completo. O usuário confirmou o seletor histórico #1/#2 anteriormente.

Limitações deliberadas: as origens são agrupadas pelo texto exato do caminho; pastas aninhadas ou caminhos alternativos podem provocar contagem duplicada de arquivos físicos. Por isso o total é uma soma de inventários distintos, **não necessariamente o total de arquivos físicos exclusivos**. O histórico e o resumo superior permanecem com seus comportamentos anteriores. Nenhum arquivo ou registro é escrito nesta consulta.

## Busca paginada na biblioteca — aguardando homologação

Na seção **Biblioteca catalogada**, a GUI possui campos **Nome/caminho** e **Extensão**, além de **Limpar busca**. Uma pesquisa por `ventilador` procura esse termo no caminho relativo, inclusive pastas; extensão `pdf` ou `.pdf` aplica filtro exato. Filtros de categoria e snapshot histórico também são respeitados. `%` e `_` são tratados como caracteres literais, não como curingas. A busca é realizada exclusivamente no SQLite via `query_catalog_page()`, com paginação de 50 resultados. Não há revarredura nem alteração do banco. O agente Ollama ainda não tem uma ferramenta de busca nesta revisão.

## Busca com agente Ollama — integração experimental

A ferramenta `buscar_arquivos_catalogo` está disponível ao Qwen3 pela interface, via dispatcher de ferramentas autorizado. Ela reutiliza a busca paginada SQLite; aceita nome/caminho, extensão e categoria e limita cada página a 20 arquivos (padrão 10). O agente usa o snapshot global mais recente salvo, **não** a seleção atual do histórico, a menos que a ferramenta receba um `scan_id` explícito. As respostas geradas devem ser verificadas no painel de ferramentas utilizadas. Nenhuma operação de escrita foi acrescentada.

## Correção de usabilidade — abas funcionais (aguardando validação)

A tela anterior empilhava todas as seções e escondia **Agente Ollama local** abaixo do limite do monitor. A interface foi reorganizada em **QTabWidget**, com quatro abas: **Visão geral** (catálogo SQLite e origens), **Inventário** (seleção, prévia e catalogação confirmada), **Biblioteca** (histórico, pesquisa e paginação) e **Agente IA** (modelo, pergunta, resposta e ferramentas). O indicador de status permanece visível na parte inferior. Tamanho inicial ajustado de 960×1020 para 960×760, com mínimo 760×540. Não foi alterada a lógica de inventário, SQLite, Ollama ou permissões de arquivos.

A separação por abas é um ajuste estrutural de acessibilidade, **não o redesign visual definitivo**. **Homologado no Windows pelo usuário em 2026-11-21:** a interface abriu corretamente em quatro abas. Próxima validação: solicitar busca pelo Qwen3 na aba Agente IA.

## Busca por nome-base e ordenação por data — nova etapa

**Implementada em código; pendente de homologação no Windows.** A aba Biblioteca dispõe do seletor **Pesquisar em: Caminho completo / Somente nome**, filtros de modificação **de / até** (formato `AAAA-MM-DD`) e ordenação **Nome / Mais recentes / Mais antigos**. A tabela inclui a coluna **Modificado (UTC)**. Tudo funciona sobre o snapshot escolhido, com paginação de 50 itens e abertura SQLite `mode=ro`.

A busca por nome-base ignora o caminho de pastas: `BACKUPS/relatorio.pdf` não corresponde a `backup` no modo Somente nome, mas `BACKUPS/backup_original.pdf` corresponde. A busca por caminho mantém o comportamento atual. A data consultada é o `modified_utc` armazenado na varredura, não data EXIF, data de criação, data de compactação nem data do próprio snapshot. Os intervalos são inclusivos por data UTC; `2025-01-01` até `2025-12-31` inclui ambos os dias.

**Organização cronológica física em pastas ano/mês:** explicitamente planejada, mas não executada nesta fase. Exigirá um planejador dedicado, prévia de conflitos, aprovação e trilha de auditoria.

## Configurações — formato de data (aguardando homologação)

A quinta aba **Configurações** reúne preferências globais da interface. Primeira opção: **Formato de data** — Brasileiro `DD/MM/AAAA` (padrão inicial), Internacional ISO `AAAA-MM-DD` e Norte-americano `MM/DD/AAAA`. Essa distinção evita chamar ISO de formato americano.

A escolha é salva automaticamente em configuração **INI de usuário pelo QSettings**, fora do banco e do repositório. Ao reabrir o ArchivIA, a opção é restaurada. A Biblioteca aplica o formato aos dois campos de período e à coluna **Modificado (UTC)**; alterar o formato converte datas válidas já digitadas e reexibe as datas da tabela. Os horários permanecem indicados como UTC, sem conversão de fuso.

A pesquisa continua usando valores internos ISO `AAAA-MM-DD` e `modified_utc`; nenhuma data é alterada no SQLite nem nos arquivos. Exemplo para filtrar todo o ano de 2024: `01/01/2024` até `31/12/2024` no modo Brasileiro. Datas incompletas ou inválidas são rejeitadas antes da busca.

Para testar: `git pull`, rodar testes, abrir GUI, mudar preferência para EUA, voltar à Biblioteca e conferir o formato, fechar e reabrir; depois trocar para Brasileiro e testar um intervalo de 2024. Preferências adicionais serão consideradas posteriormente. O histórico bruto e a saída de diagnóstico do agente podem continuar usando ISO nesta primeira etapa.

## Digitação automática dos separadores de data — aguardando homologação

Os dois campos **Modificado de / até** usam máscaras Qt de entrada conforme a preferência regional: ao digitar `01012024` em Brasileiro, a interface insere `01/01/2024`; em Internacional, `20240101` resulta em `2024-01-01`; em EUA, `12312024` resulta em `12/31/2024`. Não é necessário digitar `/` nem `-`. A troca de preferência também troca as máscaras e converte datas válidas já preenchidas. Campo totalmente vazio é aceito, mesmo que Qt devolva os separadores da máscara; uma data parcial é rejeitada na consulta.

A máscara facilita a digitação, **não valida sozinha se a data existe**; a rotina `parse_user_date()` continua validando dias, meses e anos antes de consultar SQLite. Os dados persistidos permanecem ISO 8601 UTC.

## Planejador por data — motor pronto para testes

Implementação experimental em `src/archivia/planner.py`, função `propose_date_moves()`. Calcula caminhos futuros `AAAA/MM` com base na modificação UTC e verifica conflitos; não cria subpastas nem move arquivos. Restrito a mídias e 100 propostas por consulta. **Ainda não há controle gráfico para esta função**; primeiro executar testes da suíte local Windows. A preferência de data em Configurações afeta exclusivamente a visualização, não a organização temporal simulada.

## Planejamento posterior

- Seletor de pastas, botão para inventário com prévia e confirmação de gravação no SQLite.
- Listagem de arquivos por páginas, com filtros e sem JSON enorme na tela.
- Aprimorar visual, gestão de modelos, histórico de conversa e depois reconhecimento visual.
- Implementar executor de arquivos em componente separado somente após aprovação/auditoria e testes abrangentes.
