# ArchivIA — Escopo mínimo, prioridades e contenção de complexidade

**Decisão de produto:** o ArchivIA é um **bibliotecário digital local**, não um gerenciador genérico com dezenas de recursos. A meta é **encontrar, classificar, planejar e organizar arquivos com segurança**, usando IA local como apoio opcional. Este documento delimita escopo e prioriza manutenção; **não autoriza execução sobre arquivos**.

## Fluxo principal que queremos entregar

1. **Escolher origem** e examinar seus arquivos sem modificá-los.
2. **Catalogar e encontrar** por nome, extensão, categoria e data, com histórico quando útil.
3. **Classificar com assistência da IA local**, quando necessário, distinguindo metadados de reconhecimento real de conteúdo. Atualmente a classificação é essencialmente por extensão; a semântica não está implementada.
4. **Definir organização desejada**, com categorias/destinos e eventuais regras de nomenclatura; hoje há apenas simulações parciais e regra cronológica.
5. **Revisar uma prévia explicável**, destacando arquivos, conflitos e possíveis consequências.
6. **Autorizar operação real com segurança**, em etapa futura específica, incluindo revalidação de arquivos, registro auditável e estratégia de recuperação. **Não existe executor** na versão atual.

A operação real não deve ser antecipada para resolver lacunas de UX.

## Inventário do que já existe

| Área | Situação na implementação | Decisão |
|---|---|---|
| Inventário por extensão, metadados e categorias | Funcional, sem abrir conteúdo de mídia | **Núcleo — manter** |
| SQLite com snapshots e consultas paginadas | Funcional | **Núcleo — manter** |
| Busca por nome/caminho/extensão/data e ordenação | Funcional | **Núcleo — manter** |
| Agente Ollama local com allowlist e chamadas limitadas | Funcional para consultas e simulações, sem execução | **Núcleo Standard — manter enxuto** |
| Planejamento de organização cronológica com validação | Simulação validada | **Núcleo — consolidar**, não ampliar regras sem casos de uso |
| Planejador genérico `propose_moves` | Simulação de consolidação para pasta única; agora usa **uma página SQLite** limitada a 100 arquivos e aceita snapshot opcional | **Núcleo — manter enxuto**; uma página não equivale ao plano completo |
| SHA-256 por amostra e global | Ambos homologados com dados sintéticos | **Auxiliar — congelar expansão** |
| Sessão SHA-256 progressiva em RAM | Suíte atual de 84 testes homologada; sem GUI | **Motor experimental — manter desacoplado**, sem novos botões agora |
| Preferência de datas | Implementada | **Configuração mínima — manter** |
| Classificação semântica/visual | Ainda não implementada | **Lacuna central para planejar depois do fluxo mínimo** |
| Regras flexíveis de organização e renomeação | Ainda não implementadas | **Lacuna central; especificar antes de codificar** |
| Executor real com aprovação/recuperação | **Inexistente** | **Futuro, sujeito a análise de segurança** |

## Contenção de escopo

- **Não criar** novas abas, modos, agentes, caches, checkpoints, formatos de exportação, serviços de rede ou dependências só porque são tecnicamente possíveis.
- **Não avançar** SHA-256 (mais limites, opções ou interface progressiva) sem demonstração de necessidade real para o fluxo principal.
- Não integrar modelo de visão, embeddings nem reconhecimento avançado antes de especificar como suas classificações serão revisadas pelo usuário e utilizadas no plano.
- Preservar uma só base Python e perfis opcionais de instalação; não duplicar motor para Standard/Lite.
- Todas as funções sobre mídia real continuam proibidas até existir contrato verificável, aprovação explícita e recuperação.
- As fixtures, mocks e saídas de teste continuam isolados em `tests/`, com marcadores `TEST-ONLY` e `MOCK-ONLY`.

## Problemas de manutenção identificados nesta revisão

1. `src/archivia/gui.py` contém aproximadamente **1.400 linhas** e administra seis abas e várias consultas; separar por responsabilidades quando houver redesign, **sem** recriar regras de negócio nem reescrever tudo de uma vez.
2. `src/archivia/planner.py` mantém `propose_moves()` para destino único e `propose_date_moves()` para AAAA/MM. O primeiro já não carrega o catálogo inteiro: consulta apenas uma página SQLite de até 100 propostas. Há validações semelhantes, mas não abstrair prematuramente; preservar testes e formatos de retorno. Uma prévia parcial **não valida colisões entre todas as páginas**.
3. `src/archivia/duplicates.py` contém estratégias de amostra e de candidatos globais; `duplicate_sessions.py` adiciona outra estratégia experimental. Não gerar um quarto modo; documentar quando usar cada um e priorizar simplicidade da interface.
4. O `README.md`, `docs/GUI.md`, `docs/ARCHITECTURE.md` e `docs/EDITIONS.md` contêm **passagens historicamente válidas, mas hoje desatualizadas** (por exemplo, recursos já implementados ainda descritos como futuros). Uma revisão editorial posterior deve separar histórico de estado atual, sem apagar decisões úteis.
5. As regras atuais de organização são concentradas em mídias e por modificação UTC; o objetivo original inclui categorias variadas, renomeação e destinos escolhidos pelo usuário. **Não presumir** que AAAA/MM resolverá todos os casos.

## Especificação vigente de planejamento de grandes acervos

Para consolidar arquivos de subpastas em destino único, consultar o **contrato proposto em [ARCHITECTURE.md](ARCHITECTURE.md)**. Ainda não implementado: lotes estáveis, colisões globais entre páginas, proteção contra nomes equivalentes no Windows e relatório de cobertura. Preservar a simulação de até 100 itens como prévia parcial enquanto o motor completo não estiver homologado; nenhuma execução em arquivos reais.

## Ordem de trabalho recomendada

**Fase A — consolidação (agora).** Congelar crescimento de recursos auxiliares; definir o percurso mínimo da UI, mapear redundâncias e atualizar documentação de referência. Nenhum novo mecanismo.

**Fase B — fluxo de organização.** Especificar em exemplos pequenos como o usuário seleciona arquivos, propõe categoria e destino, recebe nome sugerido, revisa conflitos e confirma escolhas. Pode ser especificado e simulado antes de criar um executor.

**Fase C — segurança operacional.** Projetar executor separado, revalidação, prevenção de sobrescrita, auditoria e recuperação. Apenas fixtures até homologação integral.

**Fase D — apresentação final.** Modularizar GUI, definir identidade visual consistente, estados semânticos, navegação e acessibilidade, sem fazer cada recurso auxiliar ganhar uma aba.

As fases não são autorização para implementar tudo: cada mudança exige necessidade demonstrada, pequena entrega e testes.

## Critério de aceite para qualquer recurso futuro

Uma proposta só deve entrar se responder claramente:

- Qual problema do **bibliotecário digital** resolve?
- É necessária ao fluxo principal ou é apenas conveniência?
- Já existe módulo que forneça a mesma capacidade?
- Pode ser implementada com biblioteca padrão e dependências existentes?
- Quais limites de segurança e testes a acompanham?
- Quanto código e custo de manutenção adiciona?
- É possível preservá-la sem tornar a UI mais complexa?

**Decisão operacional vigente:** não integrar, neste momento, novos controles de sessão SHA-256 à GUI; não adicionar componentes até consolidar o fluxo de organização.
