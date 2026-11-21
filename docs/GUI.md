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

## Interface incluída nesta etapa

- Campo com caminho do SQLite; padrão `D:/PROJETOS/archivia/data/catalogo.sqlite3` no ambiente conhecido.
- Botão **Atualizar resumo**: consulta agregada do último snapshot, em modo somente leitura.
- Campo de modelo Ollama, padrão `qwen3:8b-q4_K_M`.
- Campo de pergunta e botão **Perguntar ao agente**.
- Painel para resposta e JSON das ferramentas realmente chamadas.
- Indicador de status/erros.
- Worker em thread separada para que a janela continue responsiva durante consultas lentas.

## Limites explícitos

- Não há operação de movimentação, renomeação ou exclusão. Pedidos para organizar somente geram **simulação** pelo agente.
- Ainda não existe seletor visual de pastas, inventário acionado pela janela, visualizador de miniaturas, análise de imagem, detecção de duplicatas ou organização real.
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
5. Testar simulação pela GUI com destino `D:/PROJETOS/archivia/tests/fixtures/manual/destino`, sem executar movimentações.

## Decisão de UX registrada em 2026-11-21

O usuário aprovou a abertura da GUI como marco técnico, **mas pediu explicitamente uma reformulação visual posterior**. A janela atual é apenas bancada funcional de homologação. Planejar interface mais bonita, moderna e intuitiva, com navegação clara, organização de painéis, seleção visual de diretórios, estados de carregamento, mensagens compreensíveis, miniaturas e prévia de operações. Não priorizar polimento visual antes da validação do motor e do fluxo agente-ferramentas; não esquecer esta exigência ao avançar o produto.

## Planejamento posterior

- Seletor de pastas, botão para inventário com prévia e confirmação de gravação no SQLite.
- Listagem de arquivos por páginas, com filtros e sem JSON enorme na tela.
- Aprimorar visual, gestão de modelos, histórico de conversa e depois reconhecimento visual.
- Implementar executor de arquivos em componente separado somente após aprovação/auditoria e testes abrangentes.
