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

1. Copie a pasta `pbip-starter` para o repositório do projeto consumidor.
2. Renomeie `Starter.pbip`, `Starter.Report` e `Starter.SemanticModel` usando o mesmo prefixo.
3. Atualize:
   - `<Projeto>.pbip -> artifacts[].report.path`;
   - `<Projeto>.Report/definition.pbir -> datasetReference.byPath.path`;
   - `<Projeto>.SemanticModel/definition/database.tmdl -> database <Nome>`.
4. Adicione tabelas, relacionamentos, medidas e páginas próprias do produto.
5. Execute `python scripts/validate_powerbi_repo.py .` no repositório que adotar o validador.

## Estado de validação

A consistência estrutural e as referências relativas são validadas em CI. A abertura real no Power BI Desktop continua sendo um critério E2E separado.
