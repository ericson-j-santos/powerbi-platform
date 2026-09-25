# Demand Tracker

Painel Power BI para acompanhar demandas operacionais sem transformar o relatório em fonte de verdade.

## Fonte de verdade

O **TODO Global** continua sendo a fonte canônica. Este PBIP é apenas uma projeção analítica.

## Modos de dados

O projeto abre por padrão em `Demo`, com dados demonstrativos versionados para CI/E2E.

Para usar o TODO Global real:
1. abra `DemandTracker.pbip`;
2. em **Transformar dados > Gerenciar parâmetros**, altere `TodoSourceMode` para `Postgres`;
3. mantenha `TodoPostgresServer=localhost:55432` no PC24x7 ou informe o endpoint autorizado do ambiente;
4. informe `TodoPostgresDatabase` — no runtime DEV canônico, `todo_global_bus_dev`;
5. configure as credenciais PostgreSQL no próprio Power BI/Fabric;
6. atualize o modelo.

No runtime PC24x7, a porta PostgreSQL destinada ao Power BI deve ser publicada **somente em loopback** (`127.0.0.1`), nunca em `0.0.0.0` ou interface de rede externa.

Nenhum usuário, senha, token ou connection string com segredo é versionado.

## Página

**Demandas Operacionais** contém cinco KPIs, filtros por prioridade/estado/projeto, distribuição por estado e tabela detalhada com próxima ação e bloqueio.

## Semântica operacional

`CONCLUÍDO` não é inferido pelo Power BI. O painel somente projeta o estado gravado no TODO Global.

## Validação

O projeto recebe validação estrutural e E2E em Power BI Desktop real, vinculada ao SHA da PR.
O modo `Postgres` só é considerado validado quando houver leitura real do TODO Global no mesmo ambiente, com credenciais mantidas fora do Git.

## Visual executivo

A página **Demandas Operacionais** usa layout executivo em 1280×720: cabeçalho contextual, cinco KPIs, filtros compactos, gráfico de distribuição por estado e tabela de ação sem sobreposição entre visuais. O canvas usa fundo neutro e os contêineres têm superfície branca, borda arredondada e destaque semântico nos KPIs críticos.
