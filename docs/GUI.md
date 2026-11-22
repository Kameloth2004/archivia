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

## Aba Organização — prévia cronológica não executável

Adicionada aba **Organização** para o planejador `propose_date_moves()`. O usuário seleciona uma pasta **destino-base já existente**, uma categoria de mídia e um snapshot (histórico atualizado pelo botão específico). A interface solicita uma simulação em thread e apresenta, numa tabela, os caminhos de origem, destinos propostos `AAAA/MM`, situação `proposto/bloqueado` e motivos de bloqueio. São exibidos **no máximo 50 arquivos** do snapshot e categoria escolhidos; a contagem de correspondências totais e o aviso de amostra parcial são apresentados.

**Nenhuma pasta de ano/mês é criada**, nenhum arquivo é movido, apagado ou renomeado. As subpastas aparecem somente no texto das propostas. Não há botão de executar ou aprovar; toda operação segue `executable=false`. O modelo de IA não recebe nova permissão. A data usada é `modified_utc` do inventário, independentemente do formato regional de exibição.

**Teste manual recomendado:** selecionar snapshot #1 de `tests/fixtures/manual` (contém `foto_teste.jpg`), definir como destino uma pasta de testes já existente, clicar em **Simular organização** e verificar uma proposta de destino conforme ano/mês da foto. Confirmar que `AAAA/MM` não foi criado. Evitar testar primeiro em pastas de produção.

## Agente IA e simulação cronológica — integração experimental

O agente Ollama agora expõe `simular_organizacao_por_data` com nome, parâmetros e limites autorizados. Na aba **Agente IA**, é possível pedir **apenas simulações** por linguagem natural, fornecendo categoria `imagem/video/audio`, caminho de destino-base **já existente** e, opcionalmente, ID de snapshot e limite até 50. Essa ferramenta não usa automaticamente os campos selecionados na aba Organização. Retorna uma prévia JSON com situações proposto/bloqueado, mas **não cria nem movimenta nada**. Testes locais com Ollama real ainda pendentes.

## Colisões e possíveis duplicatas na simulação (aguardando validação)

A aba **Organização** passou a mostrar **Possível duplicata?** e **Nome alternativo sugerido**. O motor compara apenas nome-base normalizado e tamanho de arquivos **dentro dos primeiros itens do plano**: coincidência é uma suspeita que **não comprova identidade binária**. Não lê dados de imagem, não calcula hash e não elimina arquivos. A identificação de colisões de nome leva a sugestões textuais como `foto__2.jpg` sem liberar o status bloqueado, reservar nomes ou executar qualquer ação. Os contadores também se limitam à amostra de até 50 arquivos da GUI, não ao acervo completo.

## Redesign funcional da aba Organização — aguardando homologação

Por solicitação do usuário, a tabela de seis colunas ficou visualmente truncada. A aba foi reorganizada em **três áreas**: (1) Parâmetros da simulação, (2) Resumo com indicadores separados de Examinados, Bloqueados, Colisões e Suspeitas e (3) Arquivos e destinos propostos.

A tabela agora utiliza apenas quatro colunas principais (**Arquivo, Destino proposto, Situação, Observação**), com larguras ajustadas, linhas alternadas, rolagem horizontal quando necessária e tooltip contendo o texto completo. Ao selecionar uma linha, um painel inferior mostra **origem completa, destino completo, motivo do bloqueio, suspeita de duplicata e sugestão de nome alternativo**. A informação secundária não ocupa mais seis colunas estreitas. Continuam as mesmas ferramentas, critérios e limites de 50 arquivos; **nenhuma funcionalidade de gravação ou execução foi acrescentada**. A revisão ainda precisa de homologação visual no Windows.

## Verificação de duplicatas por SHA-256 — aguardando homologação

Dentro da aba **Organização** há agora duas subabas: **Simulação por data** e **Duplicatas (SHA-256)**. A primeira preserva o planejador já homologado; a segunda tem seu próprio seletor de categoria/snapshot e botão **Verificar duplicatas — SHA-256 (somente leitura)**. Exibe os grupos com conteúdo idêntico na amostra, quantidade de arquivos efetivamente comparados e motivos de itens ignorados.

**Limites:** até 50 arquivos por verificação na GUI, 16 MiB por arquivo e 64 MiB de leitura total. A rotina analisa somente um snapshot e primeiro identifica candidatos de mesmo tamanho; usa SHA-256 por blocos somente para esses candidatos. Arquivos isolados por tamanho não recebem hash, e arquivos fora da amostra não são verificados. A ausência de grupos repetidos **não comprova ausência de duplicatas no disco**. Não apaga, não renomeia, não move nem altera o catálogo.

**Teste manual preparado:** foi criada a pasta `tests/fixtures/sha256_demo` contendo oito arquivos sintéticos (extensão `.jpg` usada como metadado, não imagens reais). Primeiro selecione essa pasta em Inventário, faça uma prévia e confirme um novo snapshot no SQLite; depois atualize o histórico na subaba Duplicatas, escolha o novo snapshot, categoria Imagens e verifique. O cenário esperado é **2 grupos SHA-256 com 5 arquivos**: um grupo de 3 arquivos com mesmo conteúdo e nomes mistos, outro com 2 arquivos vazios. Arquivos de mesmo tamanho mas conteúdo diferente não são duplicatas. Essas fixtures só existem para os testes, nunca são arquivos de produção.

## SHA-256 ampliado com barra de progresso — aguardando homologação

A verificação de duplicatas permite configurar **Arquivos** (1–1000), **MiB/arquivo** (1–16) e **Leitura total (MiB)** (1–256). Padrões mantidos em 50 / 16 / 64. O motor consulta o snapshot fixado em lotes SQLite de até 100 arquivos, reunindo metadados da amostra antes de avaliar candidatos do mesmo tamanho e calcular SHA-256. Por isso, dois arquivos com conteúdo idêntico podem ser reconhecidos **mesmo aparecendo em páginas diferentes**. A GUI apresenta progresso de consulta do catálogo e cálculo dos hashes. O processamento permanece em thread e estritamente read-only, sem gravar hashes no SQLite.

Limites e cautela: arquivos acima do orçamento ou modificados são ignorados com motivo; uma amostra de 1000 arquivos não equivale a uma análise completa de uma biblioteca maior. O progresso é baseado em quantidades por fase, não em tempo estimado. É possível configurar limites menores para reduzir I/O em discos lentos.

**Teste sugerido:** snapshot #3 com os oito arquivos sintéticos, 100 arquivos no campo de limite: devem aparecer novamente 2 grupos, 5 arquivos idênticos e barra concluída. Os testes automatizados também criam arquivos sintéticos entre páginas 1 e 2 para validar a comparação entre páginas.

## Homologação manual de duas páginas SHA-256 — 134 arquivos

Executar na raiz do projeto `python tests/generate_sha256_paged_demo.py`. O script cria somente dados de teste em `tests/fixtures/manual/sha256_paginado`, sem sobrescrever, e não é necessário executá-lo para testes automatizados. Depois, em **Inventário**, examinar explicitamente essa pasta e salvar o snapshot mediante confirmação. Na subaba **Organização → Duplicatas (SHA-256)**, clicar Atualizar histórico, selecionar o snapshot recém-criado, categoria **Imagens**, quantidade **200**; clique Verificar. Esperado: **134 analisados, 2 lotes SQL, 3 grupos, 7 arquivos iguais, 0 ignorados**, progresso concluído. Com limite 100, aparecerá `AMOSTRA PARCIAL`, porque há 134 arquivos na categoria.

O cenário contém arquivos sintéticos com extensão `.jpg` que não são JPEGs válidos. Não utilizar tratamento visual. A rotina de hash permanece estritamente leitura. O script não remove a pasta para não apagar dados sem autorização; uma segunda execução sobre a mesma pasta será recusada.

## Dois modos de verificação SHA-256 — global em homologação

A subaba **Organização → Duplicatas (SHA-256)** oferece **Tipo de análise**:
- **Amostra por nome** (até 1.000): modo já homologado; examina apenas os primeiros registros do snapshot ordenados por caminho.
- **Candidatos em todo o snapshot** (até 5.000): novo modo, identifica **todos os grupos com tamanho repetido** no snapshot pelo SQLite read-only e seleciona grupos inteiros de candidatos dentro do limite. Isto evita perder uma cópia cujo nome está depois da primeira página, mas **não garante verificar tudo** quando há grupos maiores que o limite ou arquivos que excedem o orçamento.

As opções de MiB/arquivo e Leitura total aplicam-se aos dois modos. No modo global, o resumo distingue **candidatos encontrados no snapshot inteiro**, **candidatos efetivamente selecionados**, **grupos omitidos por limite**, **hashes lidos** e **arquivos ignorados**. A marca `GLOBAL INCOMPLETA` alerta sobre candidatos pendentes ou leituras não realizadas. Não há remoção automática de arquivos ou exportação de planos.

Para o teste: snapshot sintético #4, categoria Imagens, modo **Candidatos em todo o snapshot**, limite 200; esperar 134 candidatos, 3 grupos e 7 arquivos idênticos, sem pendências. Testar limite 50 para confirmar pendência de grupo maior que o limite, sem classificá-lo como verificado. **Pendente validação Windows.**

## Destaque do estado da verificação SHA-256 (pendente homologação)

A subaba Duplicatas possui indicador próprio de **cobertura**, distinto da barra de progresso. O término da execução sempre pode mostrar `Verificação concluída`; isso **não implica** cobertura completa. Quando há grupos de tamanho pendentes, orçamento excedido, erros ou amostra parcial, o indicador informa **GLOBAL INCOMPLETA** (ou **AMOSTRA INCOMPLETA**) em destaque âmbar e quantifica os candidatos pendentes/ignorados. Quando não há pendência, informa **VERIFICAÇÃO COMPLETA** com realce discreto. Ao iniciar nova consulta, informa **ANÁLISE EM ANDAMENTO**.

Esse destaque é melhoria pontual de clareza, não o redesign final. O projeto prevê uma etapa própria de interface visual e identidade, com hierarquia tipográfica, estados semânticos, navegação, tabelas e acessibilidade. Nenhum algoritmo SHA-256 foi modificado nesta atualização.

## Processamento progressivo — preparação do motor

Existe uma primeira implementação de sessões progressivas em `src/archivia/duplicate_sessions.py`, mas **ela ainda não está conectada à interface**. Após aprovação dos testes locais, a próxima evolução da subaba Duplicatas poderá oferecer **Iniciar sessão**, **Próximo lote** e **Encerrar sessão**, mantendo resultados acumulados na memória enquanto o aplicativo estiver aberto. O cursor fixa snapshot e categoria; alterar essas opções deverá iniciar outra sessão. Encerrar/reabrir o aplicativo perde o progresso, pois esta primeira etapa não salva checkpoints nem hashes no disco.

O indicador separado de cobertura (**GLOBAL INCOMPLETA**, **VERIFICAÇÃO COMPLETA**) já foi implementado, mas sua homologação visual permanece pendente.

## Contexto automático para consultas do agente (pendente de validação)

Na aba **Inventário**, a pasta selecionada define o contexto da aba **Agente IA**: ao enviar uma pergunta, a GUI procura o snapshot mais recente da origem exata e restringe as ferramentas do Ollama a ele, sem exigir que o usuário informe `scan_id`. Se a pasta não estiver catalogada, o usuário recebe aviso para usar **Examinar pasta** e **Salvar inventário**; não há catalogação automática, alteração de mídias ou consulta silenciosa a outra origem. Se não houver pasta selecionada, o comportamento anterior continua usando o último snapshot geral, por compatibilidade. Essa vinculação é uma primeira integração, **não** o fluxo completo de clique único nem o redesign prometido.

## Planejamento posterior

- Seletor de pastas, botão para inventário com prévia e confirmação de gravação no SQLite.
- Listagem de arquivos por páginas, com filtros e sem JSON enorme na tela.
- Aprimorar visual, gestão de modelos, histórico de conversa e depois reconhecimento visual.
- Implementar executor de arquivos em componente separado somente após aprovação/auditoria e testes abrangentes.
