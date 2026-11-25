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
