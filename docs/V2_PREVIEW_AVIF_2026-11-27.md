# ArchivIA V2 — Correção de prévias AVIF e formatos Qt não reconhecidos

Data: 27/11/2026. Branch isolada derivada de `develop/v2.0.0`.

## Falha diagnosticada

A versão anterior de `gui_viewer._ImageLoad.run()` confundia `QImageReader.size()` inválido (muitas vezes um codec indisponível) com a condição de pixels acima do teto. Assim, arquivos AVIF pequenos podiam apresentar "Dimensões indisponíveis ou acima do limite de segurança", mesmo sem chegar ao teste de dimensões.

## Alteração

- `image_decode.decode_preview()` tenta abrir pelo Qt como primeira opção.
- Se Qt não consegue identificar dimensões ou decodificar, tenta **Pillow opcional** no mesmo arquivo; inclui AVIF, PNG, JPEG, TIFF etc, conforme formatos efetivamente suportados pela instalação.
- Pillow 11.3+ oferece AVIF nos wheels Windows x64; não é garantido em instalações antigas e alguns sistemas.
- A saída é `QImage` independente da memória Pillow (cópia), e a imagem reduzida respeita `max_side`. A dimensão original continua disponível no visualizador.
- Mantidos os controles de identidade e de não modificação do arquivo antes/depois da leitura.
- O erro agora distingue ausência de decodificador, arquivo inválido e dimensões realmente acima do teto.

## Limites

`PREVIEW_MAX_SOURCE_PIXELS=100_000_000` e `PREVIEW_MAX_SIDE=4096` permanecem: limitam o custo de descompressão/visualização e não correspondem à capacidade do monitor. `PREVIEW_MAX_BYTES=80 MiB` continua como teto defensivo inicial. A escolha é revisável mediante requisitos e benchmark, mas **remover todos os limites** poderia comprometer o processo com imagens malformadas, descompressão explosiva ou consumo excessivo de RAM. Nenhuma restrição foi elevada silenciosamente.

O fallback atual é aplicado ao visualizador ampliado, **não** ao gerador de miniaturas no explorador; é uma etapa separada para evitar duplicação e threads extras antes da homologação.

## Instalação opcional

No ambiente virtual da V2:
```bash
python -m pip install "Pillow>=11.3,<13"
```

Ou, após a branch estar selecionada, `python -m pip install -e '.[gui,images]'`. A dependência `images` foi adicionada ao `pyproject.toml` sem alterar o conjunto padrão.

## Homologação pendente

```bash
git fetch origin fix/v2-avif-preview-decoder-2026-11-27
git switch -c fix/v2-avif-preview-decoder-2026-11-27 FETCH_HEAD
python -m pip install "Pillow>=11.3,<13"
python -m unittest discover -s tests -p "test_image_decode_v2.py" -v
python -m unittest discover -s tests -v
```

Abrir pela GUI uma cópia descartável do AVIF originalmente problemático e conferir a visualização, sem mover, sobrescrever ou converter o arquivo original. Se o erro persistir, registrar mensagem e checar decodificação com Pillow. **Nenhum teste Windows foi executado pelo assistente nesta branch.**
