# PBIP Starter

Projeto Power BI mínimo e reutilizável, composto por:

- `Starter.pbip`;
- `Starter.Report` em PBIR;
- `Starter.SemanticModel` em TMDL.

## Estrutura

```text
Starter.pbip
Starter.Report/
  definition.pbir
  definition/
    version.json
    report.json
    pages/
      pages.json
      b8c5fb8d635f898326c6/
        page.json
Starter.SemanticModel/
  definition.pbism
  definition/
    database.tmdl
    model.tmdl
    tables/
      _Measures.tmdl
```

O `definition.pbir` usa `datasetReference.byPath` para apontar para `../Starter.SemanticModel`. O `Starter.pbip` aponta para `Starter.Report`.

## Origem técnica

A estrutura PBIR baseia-se no Blank.Report publicado pela Microsoft Fabric CLI e nos schemas públicos de PBIP/PBIR. O template não contém dados, credenciais ou regras de negócio.

## Como consumir

Use o gerador para evitar renomeação e reescrita manual de referências:

```bash
python scripts/new_powerbi_project.py \
  --name SalesAnalytics \
  --output ../meu-projeto/powerbi
```

O nome é um identificador de 1 a 64 caracteres, começa com letra e aceita apenas letras ASCII, números e `_`.

O gerador:

- falha sem alterar o destino quando ele já existe;
- copia somente os artefatos PBIP/PBIR/TMDL necessários;
- não copia estado local `.pbi`, `localSettings.json` ou `cache.abf`;
- renomeia `Starter.pbip`, `Starter.Report` e `Starter.SemanticModel`;
- atualiza as referências PBIP → Report → SemanticModel;
- atualiza o identificador do banco TMDL;
- valida o resultado antes de publicar o diretório final.

Depois da geração, adicione tabelas, relacionamentos, medidas e páginas próprias do produto no repositório consumidor.

## Estado de validação

O starter e o fluxo de geração são validados estruturalmente em CI. O E2E do repositório gera um consumidor temporário e abre o PBIP resultante no Power BI Desktop real.
