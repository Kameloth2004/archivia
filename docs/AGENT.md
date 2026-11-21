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

## Fluxo
1. O usuário envia uma pergunta e o nome exato de um modelo instalado localmente.
2. O cliente Python envia a pergunta e a declaração das ferramentas para `http://127.0.0.1:11434/api/chat`, com `stream=false`.
3. O modelo pode solicitar no máximo 3 ferramentas em **uma rodada**. A aplicação confere nome, parâmetros e limites independentemente do modelo.
4. O resultado é devolvido como mensagem de ferramenta; em seguida é pedida uma resposta final **sem disponibilizar outras ferramentas**.
5. A resposta e os resultados são mostrados como JSON no terminal. Não são criados logs nem arquivos de conversas.

## Segurança
- O agente não recebe nenhum método de execução arbitrária de código, shell, SQL ou ações em disco.
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
- Os resultados do catálogo podem ser grandes; uma ferramenta de listagem paginada virá depois.
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

## Próxima validação
1. Executar testes com mocks (não precisam de Ollama).
2. Verificar `ollama list` e escolher um modelo instalado com tool calling.
3. Testar `resumo_catalogo` em uma única pergunta.
4. Só depois testar simulações de movimento, sempre dentro de `tests/fixtures/manual/`.
