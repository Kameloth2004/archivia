# ArchivIA — Agente local Ollama (protocolo v0)

## Objetivo
Receber instruções em linguagem natural, selecionar ferramentas autorizadas e retornar resultados sem acesso irrestrito ao sistema operacional. Em v0, **não há ferramenta para mover, renomear, apagar ou criar arquivos de mídia**.

## Arquivos
- `src/archivia/agent.py`: integração à API local do Ollama via biblioteca padrão do Python, allowlist de ferramentas e dispatcher.
- `tests/test_agent.py`: testes e mocks identificados como `MOCK-ONLY`, sem chamar Ollama.
- `docs/ARCHITECTURE.md`: arquitetura maior e contratos do motor.

## Ferramentas autorizadas
1. `resumo_catalogo({})`: consulta estatísticas do último snapshot SQLite.
2. `simular_movimentacao({categoria, destino, limite?})`: gera prévia não executável para categoria `imagem|video|audio` e destino existente.
3. `buscar_arquivos_catalogo({nome?, extensao?, categoria?, pagina?, limite?, scan_id?, escopo?, data_inicial?, data_final?, ordenacao?})`: busca por trecho literal do caminho e extensão exata, com categoria opcional e snapshot específico. Abre SQLite somente leitura e retorna uma página de no máximo 20 registros; padrão 10. `pagina` no máximo 100 por chamada.

4. `simular_organizacao_por_data({categoria, destino, scan_id?, limite?})`: **somente simula** estrutura `AAAA/MM/nome.ext` com base em `modified_utc`. Categoria `imagem|video|audio` e pasta-base já existente são obrigatórias. Snapshot opcional; limite padrão 10, máximo 50. Retorna conflitos, contagem e `executable=false`. Não cria subpastas nem move arquivos.

## Fluxo
1. O usuário envia uma pergunta e o nome exato de um modelo instalado localmente.
2. O cliente Python envia a pergunta e a declaração das ferramentas para `http://127.0.0.1:11434/api/chat`, com `stream=false`.
3. O modelo pode solicitar no máximo 3 ferramentas em **uma rodada**. A aplicação confere nome, parâmetros e limites independentemente do modelo.
4. O resultado é devolvido como mensagem de ferramenta; em seguida é pedida uma resposta final **sem disponibilizar outras ferramentas**.
5. A resposta e os resultados são mostrados como JSON no terminal. Não são criados logs nem arquivos de conversas.

## Segurança
- O agente não recebe nenhum método de execução arbitrária de código, shell, SQL ou ações em disco.
- A nova ferramenta `simular_organizacao_por_data` utiliza estritamente o planejador já homologado: valida categoria, caminho-base e limites; nunca executa as ações do JSON.
- A busca valida os parâmetros independentemente do modelo, não aceita propriedades extras, não interpreta `%` nem `_` como curingas e não altera os arquivos.
- `simular_movimentacao` reutiliza validações do planejador e nunca escreve nos arquivos de mídia.
- Instruções do usuário ou do modelo não alteram o allowlist.
- O endpoint Ollama é fixo em localhost. Não há serviços em nuvem no protocolo.
- A confirmação de aprovação não existe nesta etapa, nem um executor real.
- Um plano não é uma autorização; ignore pedidos do modelo para executá-lo.
- Não conceder ao agente execução de shell para contornar essas restrições.

## Limitações conhecidas
- A compatibilidade de tool calling depende da versão e do modelo Ollama; testar localmente.
- O formato de resposta e o uso de ferramentas variam por modelo. Alguns podem responder sem acionar ferramenta.
- Sem sessões persistentes nem memória de diálogo entre invocações.
- A nova busca limita a quantidade de resultados por página, mas pesquisas com muitas correspondências podem requerer várias solicitações; o modelo não vê todos os resultados automaticamente.
- Sem análise do conteúdo de imagens, sem embeddings e sem modelo visual integrado.
- Respostas do modelo podem ser incorretas: resultados estruturados das ferramentas são a referência.
- A prévia do planejador ainda carrega dados do último snapshot na memória.

## Uso
Após `git pull`, primeiro executar testes:

```bash
python -m unittest discover -s tests -v
```

Com Ollama ativo e modelo que suporte ferramentas, por exemplo um modelo já instalado:

```bash
python -m archivia agente "Quantas imagens há no meu catálogo?" --modelo "qwen3:8b-q4_K_M"
```

O nome acima é apenas exemplo baseado no ambiente conhecido; confirmar com `ollama list`.

## Nome do arquivo e data de modificação

A ferramenta de busca também aceita `escopo=nome|caminho`: nome considera apenas o nome-base do arquivo; caminho inclui diretórios. `data_inicial` e `data_final` aceitam `AAAA-MM-DD` e filtram pela data de modificação UTC armazenada no SQLite, inclusive nos limites. `ordenacao=nome|recentes|antigos` define a ordem dos resultados, sem alterar arquivos. Valores fora do contrato são rejeitados independentemente do modelo. O uso dessas opções com Qwen3 real ainda precisa de validação.

A palavra *organizar* é ambígua: **ordenar por data na busca é seguro**, mas mover arquivos para novas pastas por data não está disponível. Nunca declarar movimentação executada.

## Precisão dos filtros da busca

A integração real Qwen3 → SQLite foi validada: primeira consulta retornou cinco exemplos entre 2.298 correspondências **filtradas pelo próprio modelo na categoria `outro`**. Essa categoria não havia sido solicitada pelo usuário. Atualizadas as instruções do agente e a descrição de ferramenta para **não adicionar categoria, extensão nem snapshot quando não pedidos** e informar sempre `count`, quantidade de `files` e filtros efetivos. Isso melhora a orientação, mas o modelo pode continuar cometendo desvios: a conferência deve ser feita em `tools_used`. Futuramente, avaliar contrato estruturado que impeça filtros arbitrários, se necessário.

## Busca por linguagem natural — etapa experimental

Depois de validar os testes e instalar a atualização, na GUI pedir:

```text
Procure no catálogo arquivos com backup no nome ou caminho. Mostre os cinco primeiros.
```

No resultado `tools_used`, verificar ferramenta `buscar_arquivos_catalogo`, `count` total e `files` limitada a cinco se o modelo escolher `limite=5`. A ferramenta consulta o **snapshot global mais recente**, exceto se `scan_id` for enviado explicitamente pelo modelo. A seleção de histórico feita na GUI **não** é transmitida automaticamente à ferramenta. O modelo pode escolher argumentos incorretos ou não chamar a ferramenta; confirmar sempre o JSON estruturado. Não interpretar a busca como reconhecimento visual.

## Simulação cronológica por linguagem natural — validação pendente

Na aba **Agente IA**, com modelo `qwen3:8b-q4_K_M`, testar somente em diretórios descartáveis já existentes:

```text
Simule a organização por ano e mês da categoria imagem, no snapshot #1,
usando como destino-base D:/PROJETOS/archivia/tests/fixtures/manual/destino.
Mostre o destino proposto para uma imagem. Não mova nem crie arquivos.
```

A pasta `destino` precisa **existir previamente**; não a criar automaticamente por esta função. Conferir em `tools_used`: `simular_organizacao_por_data`, `mode=simulation`, `executable=false`, `scan_id=1`, `selected`/ `blocked`; verificar que o destino permanece sem subpastas novas. O modelo pode selecionar outra ferramenta ou argumentos errados; observar o JSON real antes de homologar. **A seleção de snapshot e pasta feita na aba Organização não é transmitida ao agente**: fornecê-los explicitamente no texto.

## Próxima validação
1. Executar testes com mocks (não precisam de Ollama).
2. Verificar `ollama list` e escolher um modelo instalado com tool calling.
3. Testar `resumo_catalogo` em uma única pergunta.
4. Só depois testar simulações de movimento, sempre dentro de `tests/fixtures/manual/`.
