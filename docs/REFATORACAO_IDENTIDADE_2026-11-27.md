# ArchivIA — Refatoração 2: identidade de arquivos e escopo recursivo

Data: 27/11/2026. Implementação isolada em branch para homologação.

## Interpretação de "recursivo"

- **Inventário/descoberta:** `inventory(root, recursive=True)` percorre subpastas e registra caminhos relativos. `recursive=False` limita aos arquivos diretamente na raiz. A varredura utiliza pilha iterativa, não recursão da pilha de chamadas Python. Links simbólicos são ignorados.
- **Planejamento:** `propose_recursive_consolidation(..., recursive=True)` consulta o snapshot catalogado e propõe a consolidação dos arquivos elegíveis em uma pasta existente, respeitando escopo e limites; prévia parcial não autoriza execução.
- **Integridade/execução:** SHA-256 se calcula por arquivo. O executor supervisionado recebe cada caminho relativo da prévia, revalida origem/destino e não faz descoberta independente de pastas enquanto movimenta.
- **Utilitário de identidade:** `file_identity(stat)` é puro e **não recursivo**; ele apenas extrai quatro atributos de um arquivo para auxiliar verificações locais. Uma ferramenta de hash não precisa varrer diretórios por conta própria.

## Alterações neste PR

Criado `src/archivia/file_identity.py` com `file_identity()`, que retorna `(st_dev, st_ino, st_size, st_mtime_ns)`, sem efeitos colaterais. O helper substitui implementações literalmente equivalentes de `_identity` em `manual_copy.py` e `move_pipeline.py`, e `_file_identity` em `manual_pilot.py`.

Os mecanismos de hash, limite de tamanho, links/junctions, journal, publicação, rollback e exclusão continuam como estavam. Não houve modificação em `move_executor.py`, `gui.py`, `gui_worker.py`, CLI ou ferramentas do agente Ollama.

## Testes adicionados

`tests/test_file_identity.py` caracteriza:
1. compatibilidade do retorno com os quatro atributos originais do `os.stat_result`;
2. inventário recursivo de dois níveis e comparação com `recursive=False`;
3. não percorrer um diretório por link simbólico (ignorado quando o sistema não permite criar symlink).

## Validação pendente

No Windows, na raiz do repositório:

```bash
git fetch origin
git switch refactor/shared-file-identity-2026-11-27
python -m unittest discover -s tests -v
```

Não foi executada a suíte Windows pelo assistente. A ausência de falhas em testes de unidade não certifica a segurança de movimentações reais, recuperação após interrupção, atomicidade ou comportamento sob alterações externas concorrentes.

## Próxima etapa

Comparar formalmente contratos de **hash e journal** entre módulos, documentando pré-condições, limites e garantias de publicação/recuperação antes de extrair mais código comum. Não migrar/excluir protótipos sem cobertura e rastreio de dependências.
