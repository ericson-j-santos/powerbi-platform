# Semantic Model Starter

Template mínimo e reutilizável de modelo semântico Power BI em TMDL.

## Base técnica

- `definition.pbism` versão 4.2;
- TMDL em `definition/`;
- compatibilidade Power BI;
- tabela calculada `_Measures` sem dependência de fonte externa.

## Uso

1. Copie `Starter.SemanticModel`.
2. Renomeie a pasta para `<Projeto>.SemanticModel`.
3. Ajuste o nome do banco em `definition/database.tmdl`.
4. Adicione tabelas e referências no `definition/model.tmdl`.
5. Remova a tabela `_Measures` apenas se houver outra tabela para hospedar as medidas.

Este template não contém credenciais, dados ou regras de negócio.
