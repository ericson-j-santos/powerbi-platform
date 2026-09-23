# Demand Tracker

Painel Power BI para acompanhar demandas operacionais sem transformar o relatório em fonte de verdade.

## Fonte de verdade

O **TODO Global** continua sendo a fonte canônica. Este PBIP é apenas uma projeção analítica.

## Modos de dados

O projeto abre por padrão em `Demo`, com dados demonstrativos versionados para CI/E2E.

Para usar o TODO Global real:
1. abra `DemandTracker.pbip`;
2. em **Transformar dados > Gerenciar parâmetros**, altere `TodoSourceMode` para `Postgres`;
3. informe `TodoPostgresServer` e `TodoPostgresDatabase`;
4. configure as credenciais PostgreSQL no próprio Power BI/Fabric;
5. atualize o modelo.

Nenhum usuário, senha, token ou connection string com segredo é versionado.

## Página

**Demandas Operacionais** contém cinco KPIs, filtros por prioridade/estado/projeto, distribuição por estado e tabela detalhada com próxima ação e bloqueio.

## Semântica operacional

`CONCLUÍDO` não é inferido pelo Power BI. O painel somente projeta o estado gravado no TODO Global.

## Validação

O projeto recebe validação estrutural e E2E em Power BI Desktop real, vinculada ao SHA da PR.
