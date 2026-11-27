# ArchivIA V2 — Biblioteca Digital Universal

Branch exclusiva de desenvolvimento: `develop/v2.0.0`.
Versão inicial: `2.0.0.dev0`.

A linha estável V1 permanece preservada em `release/v1.0.0`; a `main` não deve
receber mudanças da V2 antes da homologação.

## Navegação modular (primeira etapa)

A interface V2 utiliza seis abas permanentes:

1. **Início**: escolha da origem, análise inicial, consulta rápida opcional
   e atalho para Organizar.
2. **Biblioteca**: *Acervo* (busca e filtros), *Inventário* (prévia e
   catalogação) e *Visão geral* (origens e snapshots no SQLite).
3. **Documentos**: atalhos para consultar documentos, planilhas e
   apresentações por categoria ou extensão no Acervo. Esses atalhos não
   extraem texto nem abrem o conteúdo dos arquivos.
4. **Organizar**: *Movimentação*, *Simulação por data* e
   *Duplicatas (SHA-256)*. Reutiliza as operações e autorizações existentes.
5. **Agente IA**: consulta local ao Ollama e suas ferramentas de leitura
   e simulação, sem executar movimentações.
6. **Configurações**: seleção do modelo Ollama e preferências de data.

O antigo botão *Avançado* foi substituído pela navegação permanente.
A aba Documentos ainda não possui leitor de metadados interno,
renomeação nem análise de conteúdo: nesta etapa, são apenas acessos
a filtros do catálogo existente.

Os resultados da organização são exibidos também em Organizar, sem
criar uma segunda fila ou duplicar o motor de movimentação. A tela
de Início não contém mais os botões de autorização para mover.

## Painel Início compacto e origem única

Na interface maximizada, a **pasta ativa da sessão** no cabeçalho é a
única seleção de origem apresentada no Início. O campo duplicado
*Pasta de origem* e seu botão *Escolher pasta* foram retirados dessa área.
Os handlers existentes continuam reutilizando o mesmo controle de origem
do Inventário; nenhum segundo estado de pasta foi criado.

O Início concentra **Analisar pasta ativa e subpastas**, o acesso à
organização e o resumo da última análise. A caixa de aviso redundante
foi removida e o espaço flexível passou para o fim do layout, de modo
que o monitor maximizado não estique os blocos informativos.

A seleção de destino permanece exclusivamente no fluxo Organizar.
O futuro explorador de arquivos e suas miniaturas pertencerão à Biblioteca,
sem sobrecarregar o Início.

## Faixa global compacta e análise recolhível

A pasta ativa tem um campo de largura limitada na faixa superior do ArchivIA.
Na mesma linha permanecem **Escolher pasta**, **Limpar**,
**Analisar pasta e subpastas** e **Organizar arquivos**. Esses botões
reutilizam os handlers existentes e não criam outros estados de origem.
Quando a opção de organização é utilizada, abre a área Organizar da
navegação lateral, sem movimentar arquivos automaticamente.

Na área Início, **Consultas e catalogação** continua opcional e recolhida
por padrão. O relatório principal também fica recolhido inicialmente,
sob **Análise e resultados (ver detalhes)**; após a análise, seu título
passa a **Análise concluída (ver detalhes)**. Abrir ou recolher o painel
não descarta o relatório, que continua espelhado na aba Organizar.
As informações operacionais e de erro continuam disponíveis mediante
abertura explícita do painel.

O objetivo é reservar a região central para o futuro Explorador Visual
da Biblioteca, preservando as confirmações e o isolamento do catálogo.

## Relatório de análise sem rolagem aninhada

O painel recolhível **Análise e resultados** utiliza `ExpandingReport`,
um controle somente leitura com altura determinada pelo texto exibido.
Ao abrir, suas linhas são apresentadas integralmente e não há barra de
rolagem vertical própria do campo. Ao recolher, o relatório permanece
em memória para consultas posteriores.

Caso um relatório longo exceda a área disponível na janela, a rolagem
permanece na página **Início** (`QScrollArea`), evitando o corte de dados.
A aba **Organizar** continua com seu relatório independente; o ajuste
é apenas de apresentação, sem efeitos sobre inventário, movimentações
ou catálogo persistente.

## Janela maximizada e navegação à esquerda

A V2 inicia com `showMaximized()`, respeitando a área útil do monitor
e a barra de tarefas do Windows; não usa tela cheia exclusiva. As seis
áreas principais aparecem como comandos verticais à esquerda, com ícones
e seleção destacada. Um divisor redimensionável `QSplitter` separa
a coluna de navegação da área de trabalho.

O `QTabWidget` permanece internamente para preservar os atalhos já
homologados que selecionam áreas por índice ou widget, enquanto a barra
horizontal principal fica oculta. As subabas da Biblioteca e da
Organização permanecem visíveis no conteúdo. Nenhum comando da coluna
lateral inicia inventários ou movimentações.

Esta etapa não inclui ainda o explorador de miniaturas. Homologar a
navegação, a distribuição do espaço e o comportamento de restaurar e
maximizar antes de acrescentar os painéis visuais.

## Campos de data no Acervo

Os filtros **Modificado de** e **até** na Biblioteca → Acervo aceitam
digitação manual com máscara e também seleção pelo ícone de calendário.
O menu inclui **Limpar data** para desativar o filtro, sem usar datas
fictícias. Selecionar ou limpar uma data solicita nova consulta ao
catálogo; nenhuma movimentação ocorre.

As preferências existentes da aba Configurações continuam suportadas:
DD/MM/AAAA, AAAA-MM-DD e MM/DD/AAAA. Uma troca de formato preserva o
mesmo dia selecionado. O backend continua recebendo data ISO e consultando
a data de **última modificação**, não a de criação.

## Pasta ativa compartilhada na sessão

O campo **Pasta ativa da sessão**, abaixo do cabeçalho, define a origem
para Início, Inventário, Organizar, Documentos e Agente IA. A pasta
continua selecionada ao alternar abas. **Limpar** encerra o contexto
temporário. A seleção não é armazenada nas preferências do Windows,
não é enviada ao Ollama por si só e desaparece ao fechar o programa.

Em **Biblioteca → Acervo → Consultar**, escolha explicitamente:

- **Catálogo salvo (SQLite)**: consulta os snapshots anteriores com histórico
  e filtros, sem ficar automaticamente restrito à pasta ativa.
- **Pasta ativa (sessão)**: consulta apenas o snapshot temporário dessa pasta
  e suas subpastas. Clique em **Listar catálogo** para a primeira consulta,
  ou **Atualizar pasta ativa** para refazer o inventário e consultar novamente.

Os atalhos da aba Documentos abrem os filtros do Acervo, respeitando
a fonte escolhida. Uma consulta da pasta ativa não grava snapshots no
SQLite persistente. Para salvar um inventário, utilize explicitamente
a opção de catalogação da Biblioteca → Inventário.

Ao mudar ou limpar a pasta, a prévia, a seleção de movimentos e o catálogo
temporário antigos são invalidados. Após uma movimentação, a pasta continua
selecionada, mas a análise temporária é invalidada: uma próxima consulta
faz novo inventário. Alterações externas realizadas fora do ArchivIA
exigem **Atualizar pasta ativa**; a seleção de pasta não implica monitoramento
contínuo do disco.

## Categorias organizáveis

O inventário já reconhece os nove grupos abaixo. A V2 habilita a seleção
desses mesmos grupos tanto na organização supervisionada da tela Início
quanto nas simulações de organização por data e no agente local.

| Categoria interna | Interface | Exemplos |
| --- | --- | --- |
| imagem | Imagens | jpg, png, webp, avif |
| video | Vídeos | mp4, mkv, mov |
| audio | Áudios | mp3, wav, flac |
| documento | Documentos | pdf, docx, txt, md, epub |
| planilha | Planilhas | xlsx, csv, ods |
| apresentacao | Apresentações | pptx, odp |
| compactado | Compactados | zip, rar, 7z, tar |
| codigo | Código-fonte | py, php, js, json, sql |
| outro | Outros arquivos | extensões não mapeadas e arquivos sem extensão |

As categorias são determinadas **exclusivamente pela extensão**. O programa
não lê, abre, interpreta, executa ou extrai o conteúdo desses arquivos para
decidir a categoria. Arquivos de extensão desconhecida, inclusive executáveis,
podem aparecer em **Outros arquivos**; selecione e confirme conscientemente.

Cada planejamento organiza **uma categoria por vez**. A opção de reunir
simultaneamente todos os tipos em uma única operação não foi introduzida aqui:
exige projeto específico para os destinos e prevenção de colisões globais.

## Segurança preservada

- A prévia não move arquivos; movimentações dependem de aprovação explícita.
- Os destinos precisam existir. A operação não cria pastas arbitrariamente.
- Nunca há sobrescrita. Conflitos de nomes bloqueiam a execução automática.
- O SHA-256 valida a cópia antes da eventual remoção da origem.
- A verificação do arquivo e dos caminhos acontece novamente na execução.
- A seleção **Incluir subpastas** mantém o comportamento V1. Desmarcada,
  analisa e organiza somente arquivos diretamente na pasta escolhida.
- Arquivos dentro da pasta de destino, quando esta fica dentro da origem,
  não entram novamente no plano.
- Arquivos ZIP, scripts e executáveis são tratados como bytes de arquivos:
  o ArchivIA não abre ou executa seus conteúdos.

## Homologação no Windows

Dentro de `D:\\PROJETOS\\archivia_v2`, com ambiente virtual ativo:

```bash
git pull origin develop/v2.0.0
python -m unittest discover -s tests -v
archivia-gui
```

Realize primeiro a prévia em uma pasta descartável com amostras dos grupos.
Confirme a opção **Incluir subpastas** em ambos os estados.
Valide bloqueios de nomes duplicados e verifique se o resultado dos
movimentos preserva os bytes e os documentos existentes.

O selo `V2 · Desenvolvimento` aparece à direita do rodapé; a janela também
é identificada como ArchivIA V2.

## Conflitos entre nomes-base no planejamento e na fila

Ao reunir arquivos de diferentes subpastas em um único destino, dois
`README.md` ou nomes equivalentes com diferenças de maiúsculas/minúsculas
não podem ser escolhidos automaticamente. A V2 marca **todas as ocorrências
que disputam o mesmo nome-base como bloqueadas**, antes da execução.

Esses arquivos não são excluídos nem sobrescritos. Outros arquivos com
nomes livres continuam disponíveis para mover. Se um plano anterior ou
alterado apresentar uma proposta com nome ambíguo, o executor registra
o item como bloqueado e a fila prossegue; erros imprevistos ou falhas de
integridade continuam interrompendo a operação.

O relatório final distingue:
- bloqueios detectados no planejamento, que **não entram na fila**;
- bloqueios encontrados na execução, que contam como processados;
- erros que interrompem a fila;
- arquivos pendentes, que **não foram tentados** na execução.

Se uma movimentação anterior foi interrompida, gere nova prévia antes de
continuar: arquivos já movidos não devem ser enviados novamente.

## Limitações intencionais

- Ainda não há classificação por conteúdo, IA semântica ou extração de arquivos.
- Não há movimentação simultânea de todas as categorias em um único clique.
- Não há desfazer automático de lotes concluídos.
- `outro` é uma categoria genérica, não uma autorização para executar arquivos.
