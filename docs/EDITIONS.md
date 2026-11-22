# ArchivIA — Edições e estratégia de distribuição

Atualizado em 2026-11-21. **Documento de planejamento**, não descreve instaladores existentes.

## Decisão

Manter **um único repositório, um único motor Python e contratos comuns de ferramentas**, com três perfis de instalação/uso. Evitar forks e duplicação da lógica. Segurança, planejamento, SQLite e testes devem funcionar de forma igual nos perfis que oferecem essas operações.

## Perfis planejados

| Perfil | Hardware-alvo | IA | Recursos |
|---|---|---|---|
| **ArchivIA Standard** — **prioridade atual** | Windows 10 64-bit, i5, 32 GB RAM, NVIDIA RTX 3060 12 GB | Ollama local, modelo coordenador, futura visão local | Inventário, catálogo, agente, interface desktop, futura classificação visual e organização controlada |
| **ArchivIA Lite** | PC Windows/Linux 64-bit sem GPU dedicada; meta inicial a validar: ~4 GB RAM | Não obrigatória | Inventário, catálogo, filtros, duplicatas por algoritmos clássicos, prévias e organização com aprovação |
| **ArchivIA Lite + IA** | PC 64-bit sem GPU dedicada; meta inicial a validar: ~8–16 GB RAM | Ollama local via CPU e modelo pequeno, opcionalmente serviço em outro computador confiável da rede | Lite + conversas e ferramentas autorizadas, possivelmente com latência maior |

RAM/hardware acima são **metas preliminares**, não requisitos certificados nem benchmarks. Consumo real depende do volume da biblioteca, modelo Ollama, contexto e interface. Ainda não existem executáveis nem instaladores dessas edições.

## Dependências e distribuição planejadas

- Motor: Python e SQLite (SQLite já disponível via módulo padrão `sqlite3`), sem serviços em nuvem obrigatórios.
- Interface de homologação: PySide6/Qt **já implementada** como dependência opcional; avaliar custo em RAM e tamanho do instalador futuro.
- Instalação final pretendida: empacotar runtime Python e dependências, para o usuário não precisar instalar Python manualmente.
- Ollama: opcional no Lite, necessário apenas ao habilitar agente no Lite + IA e Standard.
- Modelos: baixar/selecionar separadamente; nunca presumir que modelo esteja presente.
- Funções de IA devem falhar de maneira clara e não impedir o uso das funções básicas sem Ollama.
- Uso de Ollama pela rede local é proposta futura: requer autenticação/isolamento de rede, consentimento e verificação de superfície de exposição; não disponibilizar serviço aberto na LAN por padrão.

## Foco imediato: Standard no ambiente do desenvolvedor

**Ambiente de referência**
- Projeto: `D:/PROJETOS/archivia`.
- Windows 10 Home 22H2 64-bit.
- Intel i5, 32 GB RAM, RTX 3060 12 GB VRAM.
- Ollama local e `qwen3:8b-q4_K_M` já validados para chamadas de ferramentas.

**Ordem de trabalho**
1. Consolidar motor Python, contratos e allowlist do agente, sempre com testes e documentação.
2. Criar interface desktop inicial PySide6 que opere o motor sem depender de prompt ou GPU para inventário/consultas.
3. Preparar listagem paginada e tratamento de catálogos grandes.
4. Integrar modelos de visão locais para conteúdo de imagem, depois similaridade (hash perceptual/embeddings).
5. Projetar fluxo de aprovação e executor seguro separado, com auditoria e recuperação; não ativar movimentação antes dessas garantias.
6. Empacotar e testar versão Standard no próprio Windows.
7. **Somente depois**, medir consumo, definir requisitos e empacotar os dois perfis Lite.

Essa ordem é diretriz flexível; não significa que as etapas já estejam implementadas.

## Regras arquiteturais para suportar os três perfis

- Motor de arquivos e catálogo independentes de GUI, Ollama, GPU e infraestrutura de teste.
- Recursos opcionais ativados por detecção de capacidade e configuração explícita, não por importações obrigatórias.
- Sem cópia do motor para outra edição: perfis decidem somente quais componentes são instalados/habilitados.
- Toda operação de escrita sobre arquivos exige validação independente, aprovação explícita e trilha auditável, independentemente da edição.
- Testes/fixtures/mocks somente sob `tests/`, com marcações `TEST-ONLY` e `MOCK-ONLY`.

## Estado validado até esta decisão

- Inventário e SQLite funcionais.
- O registro inicial de 19 testes foi superado: **83 testes informados como aprovados no Windows em 22/11/2026** (`OK (skipped=1)`).
- Qwen3 executou `resumo_catalogo` com resposta correta.
- Qwen3 executou `simular_movimentacao` e retornou plano com uma proposta e zero bloqueios.
- **Nenhum arquivo de mídia foi movimentado**; não existe executor.

## Referências

- [Estado e retomada](STATUS.md)
- [Arquitetura](ARCHITECTURE.md)
- [Contrato do agente](AGENT.md)
- [Regras de testes](../tests/README.md)
