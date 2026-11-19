# Laboratório AdventureWorks — falha de memória no visual anual

**Issue canônica:** powerbi-platform #31. **Estado:** implementação em branch de teste; SQL, Desktop e Service não executados. Sem modificação do SIIAC oficial.

## Contrato
O relatório de teste usa AdventureWorksDW2022, view virtual sem armazenamento de 4,8 milhões de registros e filtro de 1/10/40/80 réplicas. Se a tabela FactInternetSales contiver 60.398 linhas, 80 réplicas representam 4.831.840 linhas. O resultado real depende da contagem na instância de laboratório. Volume alto não garante falha de memória.

**Custo adicional máximo R$ 0,00.** Nenhum workspace, servidor ou licença novos foram contratados. Não usar Docker. A execução em SQL Server ou Service exige autorização específica e comprovação do ambiente correto.

## Alternativa OLTP AdventureWorks2025 (sem criar/restaurar banco)

A [issue #27 de painel-powerbi](https://github.com/ericson-j-santos/painel-powerbi/issues/27) registra uma origem candidata `AdventureWorks2025` no Noteri, **sem prova atual** de conexão ou autorização. Ela é diferente de `AdventureWorksDW2022`, que usa a tabela `FactInternetSales`.

Para usar a origem OLTP **somente após admissão física, identidade SELECT-only e custo R$ 0,00 comprovados**:

1. Executar integralmente `sql/06_preflight_adventureworks2025.sql` em instância exclusivamente de laboratório. Conferir existência/visibilidade de `Sales.SalesOrderDetail` e `Sales.SalesOrderHeader`, contagem real e permissão de leitura. Se houver falha, não criar objetos para contornar.
2. Executar `sql/07_validar_adventureworks2025.sql` com **1 réplica**; comparar linhas, itens e vendas do ano com os totais independentes da origem, e medir janeiro/2026. Aumentar para 10/40/80 somente após validar impacto e orçamento.
3. Em um **PBIX novo**, criar o parâmetro inteiro `QtdeReplicas=1` e usar `powerquery/05_adventureworks2025_sem_view.pq` como `FatoLaboratorio`. Substituir `SERVIDOR_SQL_LAB` pelo servidor de LAB; não utilizar dados do SIIAC.
4. Fazer o cenário **A** (tabela detalhada mensal e anual) e o **B** (visual agregado no mesmo modelo). Usar os mesmos filtros, escala e origem. **Não usar a consulta otimizada `02_otimizado.pq` nessa fonte**: ela consulta o DW2022; a variante C OLTP ainda não está versionada/validada.
5. O campo `ValorVenda` de 2025 usa `LineTotal` arredondado por **linha** a quatro casas; não corresponde necessariamente a `SalesOrderHeader.TotalDue` ou ao total de vendas do modelo DW2022. Comparar só com a consulta SQL 07 e a mesma regra.

### Identidade e comparabilidade das evidências

Cada CSV de medições deve conter **uma única** `origem_id` estável e sanitizada, vinculada à instância+banco efetivos (por exemplo `aw2025-lab-a` ou `awdw2022-lab-a`). O avaliador bloqueia origem ausente ou mista; registrar a identificação real da conexão somente em evidência protegida, não no Git público. Executar A/B/C em arquivos separados por origem, sem misturar resultados. O identificador no CSV não prova autenticidade: exige leitura independente da conexão real e do workspace.

## Procedimento — rota recomendada sem DDL

1. Instância SQL **exclusivamente de laboratório**: executar integralmente `sql/01_preflight.sql`. Se o estado não for `PRECONDICOES_VALIDAS`, não avançar. A conta deve ter somente `CONNECT` e `SELECT` necessários.
2. Executar `sql/05_validar_sem_view.sql` inicialmente com **1 réplica**, em sessão LAB autorizada. A consulta não cria objeto algum e fornece janeiro, ano e total independente na origem. Conferir as duas saídas. Aumentar para 10/40/80 somente com recursos e custo zero comprovados.
3. Criar um **PBIX novo**, nunca reutilizar o SIIAC oficial. No Power Query, criar parâmetro `QtdeReplicas` como número inteiro = 1, e inserir `powerquery/04_sem_view_somente_leitura.pq` como consulta `FatoLaboratorio`. Substituir somente `SERVIDOR_SQL_LAB` pela instância SQL de LAB e usar modo Import. A consulta aplica um `SELECT` parametrizado via `Value.NativeQuery` — dispensa `CREATE VIEW` e permissão de DDL.
4. Confirmar que os números da consulta M correspondem ao SQL, sem inferir sucesso somente de um carregamento. Com `EnableFolding = true`, **o folding não é garantido**: conferir `Exibir consulta nativa`/plano do Power Query e SQL enviado efetivamente ao servidor. Se o conector não dobrar filtros posteriores, tratar como bloqueio de desempenho, não como sucesso.
5. **Alternativa com view (somente se necessária e especificamente autorizada):** `sql/02_criar_view.sql`, `sql/03_validar.sql` e `powerquery/01_base.pq`. A view modifica o esquema do banco LAB; portanto NÃO é requisito da rota recomendada.
6. Criar DimCalendario, AnoMes e medidas conforme dax/01_medidas.dax. Montar segmentador DimCalendario[Date] e visual de tabela com DataMovimento, LinhaUnica, ObservacaoDetalhada, ProdutoID, ClienteID e medida Vendas.
7. Executar visual filtrado para janeiro/2026, depois para todo 2026. Capturar mensagem literal e diagnóstico no Analisador de Desempenho. Simulação de limites de memória no Desktop só afeta visuais, não comprova resultado no Service.
8. Correção B: **mesmo modelo/linhas/ano**, trocar somente visual por gráfico AnoMes e Vendas, com cartões Linhas/Itens. Correção C: em cópia separada, usar powerquery/02_otimizado.pq (retira colunas textuais) e repetir período e volume.
9. Teste D (distinto): usar powerquery/03_incremental.pq com parâmetros datetime RangeStart/RangeEnd; demonstrar folding e partições. Refresh incremental **não** corrige automaticamente memória de consulta DAX de visual.
10. Apenas em workspace existente de LAB, licenciamento/custo confirmados e autorização específica, publicar PBIX isolado e reproduzir no Service. Reutilizar conexão equivalente, sem acessar SIIAC oficial.
11. Preencher evidencias/MATRIZ_DE_TESTES.csv com SQL independente, DAX, erro literal, ambiente, workspace/modelo/run e prova. Executar tools/avaliar_cenarios.py; CANDIDATOS_PARA_READBACK não equivale à homologação.

## Aceite
A mesma quantidade de réplicas/ano no mesmo ambiente: janeiro retorna, ano base falha explicitamente por memória, B ou C retorna ano completo; SQL e DAX corrigidos são iguais e preservam totais SQL do ano base. O erro de atualização, consulta visual e gateway deve ser classificado separadamente. Verificar resultado e custo real antes de qualquer conclusão.

## Critério estrito de erro de memória

Uma mensagem genérica como `The visual has exceeded the available resources` não confirma, sozinha, que o limite atingido foi **memória**. Pode faltar a identificação do recurso. Para classificar o cenário anual como falta de memória, registrar a mensagem literal detalhada contendo `memory` ou `memória`, vinculada ao visual/execução. O código `0xC13E0003`, isolado, é tratado como **diagnóstico pendente**, pois pode surgir na atualização do modelo, que é um fluxo diferente. Erros de autenticação, timeout e outros limites não aprovam o teste de memória.

O avaliador marca no máximo `CANDIDATOS_PARA_READBACK`; exige-se leitura independente do relatório no Service para verificar o efeito real da alteração. Referências: [limites de consultas visuais](https://learn.microsoft.com/pt-br/power-bi/create-reports/desktop-set-visual-query-limits) e [solução de problemas de atualização](https://learn.microsoft.com/pt-br/power-bi/connect-data/refresh-troubleshooting-refresh-scenarios).

## Limitações
- Tanto a view quanto o SELECT direto calculam datas sintéticas: folding pode existir sem índice nem leitura seletiva na origem. Verificar plano/IO e tempo real.
- A consulta M sem view está apenas revisada estaticamente; o comportamento do driver SQL Server com parâmetros e filtros extras precisa de prova no Desktop.
- O relatório final ainda exige teste visual real no Desktop e Service; consultas SQL sozinhas não reproduzem erro de memória do motor DAX.
- Não há conexão com SQL/Service nesta entrega. Todos os CSVs começam em PENDENTE.
- O avaliador não autentica as evidências externas e não executa Power BI nem SQL Server.

## Fontes
- https://learn.microsoft.com/en-us/power-query/native-query-folding
- https://learn.microsoft.com/en-us/powerquery-m/value-nativequery
- https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure
- https://learn.microsoft.com/pt-br/power-bi/create-reports/desktop-set-visual-query-limits
- https://learn.microsoft.com/en-us/power-bi/create-reports/performance-analyzer
- https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure

Regras: chatgpt-operational-rules/main@58dcd4200f412a866278027ba9e433439a03f3b3. Base: powerbi-platform/main@bc2285c15b54bbef0be20be3ddb8c41160a279e8. Issue #31 (não duplicar #29, painel-powerbi #27).
