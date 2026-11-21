# ArchivIA

Bibliotecário digital local em Python, planejado para catalogar, classificar, renomear e organizar mídias com apoio do Ollama.

## Estado do projeto

**Etapa 1: inventário somente leitura.** O Ollama ainda não é utilizado. Nenhuma operação de renomeação, movimentação ou exclusão foi implementada.

### Princípios

- Python e biblioteca padrão nesta primeira etapa; nenhuma dependência de nuvem.
- Operações que alteram arquivos somente em etapas futuras, com prévia e aprovação.
- A varredura examina nomes e metadados do sistema de arquivos; **não abre o conteúdo** das mídias.
- Links simbólicos não são percorridos; falhas de acesso são reportadas, não escondidas.
- O inventário é emitido no terminal, sem gerar arquivos nos discos examinados.

## Executar

Requer Python 3.10 ou superior. Na raiz do repositório:

```bash
python -m archivia inventario "D:\\Minhas Midias"
```

Alternativamente, sem instalação, caso a pasta `src` esteja no `PYTHONPATH`:

```bash
PYTHONPATH=src python -m archivia inventario "/caminho/das/midias"
```

Para instalar em modo de desenvolvimento:

```bash
python -m pip install -e .
archivia inventario "/caminho/das/midias"
```

Para executar os testes:

```bash
python -m unittest discover -s tests -v
```

### Saída

Um objeto JSON em UTF-8, contendo `root`, `files`, `summary` e `errors`. A lista inclui apenas extensões de mídias conhecidas (imagem, vídeo e áudio). Tipos não reconhecidos são contabilizados, mas não listados. Arquivos e diretórios simbólicos são ignorados. Arquivos ocultos não são excluídos automaticamente.

Os metadados incluem caminho relativo, categoria baseada **somente na extensão**, extensão, tamanho em bytes e instante de modificação (UTC). Essa categorização inicial não é classificação semântica.

### Limitações desta etapa

- Inventários grandes são mantidos na memória antes de imprimir o JSON.
- O inventário pode mudar durante uma varredura; não é um snapshot atômico.
- Permissões do sistema operacional são respeitadas: leia somente diretórios de sua confiança.
- Nenhuma identificação de duplicatas por hash, reconhecimento visual ou integração com Ollama ainda.

## Próximas etapas planejadas

1. Persistência e consultas do catálogo.
2. Detecção de duplicatas e leitura controlada de metadados especializados.
3. Adaptador local Ollama para categorização semântica.
4. Plano de mudanças em modo simulação, com aprovação explícita e trilha de auditoria.
5. Organização efetiva, com medidas de recuperação e proteção contra conflitos.
