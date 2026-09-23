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

Use o gerador para evitar renomeações e referências manuais:

```bash
python scripts/new_powerbi_project.py --name MeuProjeto --output /caminho/MeuProjeto
python scripts/validate_powerbi_repo.py /caminho/MeuProjeto
```

O gerador:

1. copia somente os artefatos do starter;
2. cria `<Nome>.pbip`, `<Nome>.Report` e `<Nome>.SemanticModel`;
3. atualiza PBIP → Report → SemanticModel;
4. atualiza o database TMDL para `<Nome>Model`;
5. valida o resultado antes de publicar o diretório final;
6. falha sem sobrescrever quando o destino já existe.

O nome técnico aceita letras, números e `_`, deve começar por letra e não pode ser um nome reservado do Windows.

## Estado de validação

A consistência estrutural e as referências relativas são validadas em CI. O workflow Power BI Desktop E2E também gera um projeto temporário por este gerador e abre esse PBIP em Power BI Desktop real em runner Windows efêmero.
