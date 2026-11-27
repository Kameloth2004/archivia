# Refatoração 1 — orquestração de lote e fila (27/11/2026)

## Objetivo

Eliminar a duplicação comprovada entre `batch_move.py` e `queue_move.py`, sem alterar o executor unitário, ampliar permissões ou atribuir capacidade de movimentação ao Ollama.

## Alterações

- Adicionado `src/archivia/move_orchestration.py` com `validate_selection()` e `process_selection()`.
- `batch_move.py` mantém API `move_batch_approved()`, limite 20, nome de operação `approved_batch_move`, sem callback de interrupção e sem campo `stopped_reason`.
- `queue_move.py` mantém API `move_queue_approved()`, limite 10.000, verificação de plano com propostas ambíguas, cancelamento cooperativo antes de cada arquivo e campo `stopped_reason`.
- Ambos mantêm mensagens próprias de erro de validação, estrutura do retorno, notificações de progresso, aprovação explícita e tratamento de bloqueios seguros versus erros que interrompem a execução.
- Mantido `move_one_approved()` como único executor real invocado. Sua implementação **não foi alterada**.
- A função executor é injetada no núcleo somente pelos adaptadores Python; a camada de IA não recebeu ferramentas novas.

## Testes de caracterização

Adicionado `tests/test_move_orchestration.py` com sete métodos de teste cobrindo:
1. limites e contratos públicos de saída;
2. cancelamento antes do primeiro arquivo;
3. cancelamento entre arquivos e progresso;
4. continuação em bloqueio seguro;
5. parada em falha inesperada;
6. rejeição de ambiguidade na fila;
7. rejeição de autorização ou snapshot incorretos.

Os testes existentes `tests/test_batch_move.py` e `tests/test_large_moves.py` usam patch em `archivia.batch_move.move_one_approved` e `archivia.queue_move.move_one_approved`; os adaptadores retêm esses símbolos para compatibilidade.

**Validação pendente:** não foi possível executar o projeto em Windows via conector GitHub. Não afirmar aprovação ou contagem total atual antes de executar a suíte na estação local.

```powershell
cd D:\PROJETOS\archivia
git fetch origin
git switch refactor/shared-move-orchestration-2026-11-27
python -m unittest discover -s tests -v
```

Executar apenas com o ambiente e diretórios descartáveis previstos pela suíte, nunca com a única cópia de arquivos pessoais.

## Avaliação de segurança e limites

A remoção de código duplicado reduz risco de divergência futura, mas **não prova** segurança do executor de movimentação. Não foram reavaliados nesta etapa os mecanismos de journal, tratamento de corrida externa, persistência em falha de energia, ACL/metadados e recuperação. O limite operacional continua sendo o que a GUI e o executor unitário autorizam.

## Próxima decisão

Após testes e homologação, integrar este PR. A auditoria seguinte deve tratar dos caminhos de cópia e movimento históricos, com matriz de invariantes e dependências antes de qualquer exclusão de módulo.
