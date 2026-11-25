# ArchivIA V2 — Biblioteca Digital Universal

Branch exclusiva de desenvolvimento: `develop/v2.0.0`.
Versão inicial: `2.0.0.dev0`.

A linha estável V1 permanece preservada em `release/v1.0.0`; a `main` não deve
receber mudanças da V2 antes da homologação.

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

## Limitações intencionais

- Ainda não há classificação por conteúdo, IA semântica ou extração de arquivos.
- Não há movimentação simultânea de todas as categorias em um único clique.
- Não há desfazer automático de lotes concluídos.
- `outro` é uma categoria genérica, não uma autorização para executar arquivos.
