# Laboratório AdventureWorks — falha de memória no visual anual

**Issue canônica:** powerbi-platform #31. **Estado:** implementação em branch de teste; SQL, Desktop e Service não executados. Sem modificação do SIIAC oficial.

## Contrato
O relatório de teste usa AdventureWorksDW2022, view virtual sem armazenamento de 4,8 milhões de registros e filtro de 1/10/40/80 réplicas. Se a tabela FactInternetSales contiver 60.398 linhas, 80 réplicas representam 4.831.840 linhas. O resultado real depende da contagem na instância de laboratório. Volume alto não garante falha de memória.

**Custo adicional máximo R$ 0,00.** Nenhum workspace, servidor ou licença novos foram contratados. Não usar Docker. A execução em SQL Server ou Service exige autorização específica e comprovação do ambiente correto.

## Procedimento
1. Instância SQL de laboratório: executar integralmente sql/01_preflight.sql. Se o estado não for PRECONDICOES_VALIDAS, não avançar.
2. Inspecionar a existência da view. Só com autorização para CREATE VIEW no banco de laboratório, executar sql/02_criar_view.sql. O script bloqueia se o objeto já existe.
3. Executar sql/03_validar.sql com 1 réplica. Confirmar contagem de origem, soma de vendas, itens e datas. Aumentar progressivamente para 10/40/80 apenas se houver recursos.
4. Criar PBIX NOVO em Power BI Desktop com consulta FatoLaboratorio de powerquery/01_base.pq. Substituir SERVIDOR_SQL_LAB pelo servidor de LAB. Definir QtdeReplicas inteiro = 1; usar Import; confirmar folding. Nenhum segredo deve ser versionado.
5. Criar DimCalendario, AnoMes e medidas conforme dax/01_medidas.dax. Montar segmentador DimCalendario[Date] e visual de tabela com DataMovimento, LinhaUnica, ObservacaoDetalhada, ProdutoID, ClienteID e medida Vendas.
6. Executar visual filtrado para janeiro/2026, depois para todo 2026. Capturar mensagem literal e diagnóstico no Analisador de Desempenho. Simulação de limites de memória no Desktop só afeta visuais, não comprova resultado no Service.
7. Correção B: **mesmo modelo/linhas/ano**, trocar somente visual por gráfico AnoMes e Vendas, com cartões Linhas/Itens. Correção C: em cópia separada, usar powerquery/02_otimizado.pq (retira colunas textuais) e repetir período e volume.
8. Teste D (distinto): usar powerquery/03_incremental.pq com parâmetros datetime RangeStart/RangeEnd; demonstrar folding e partições. Refresh incremental **não** corrige automaticamente memória de consulta DAX de visual.
9. Apenas em workspace existente de LAB, licenciamento/custo confirmados e autorização específica, publicar PBIX isolado e reproduzir no Service. Reutilizar conexão equivalente, sem acessar SIIAC oficial.
10. Preencher evidencias/MATRIZ_DE_TESTES.csv com SQL independente, DAX, erro literal, ambiente, workspace/modelo/run e prova. Executar tools/avaliar_cenarios.py; CANDIDATOS_PARA_READBACK não equivale à homologação.

## Aceite
A mesma quantidade de réplicas/ano no mesmo ambiente: janeiro retorna, ano base falha explicitamente por memória, B ou C retorna ano completo; SQL e DAX corrigidos são iguais e preservam totais SQL do ano base. O erro de atualização, consulta visual e gateway deve ser classificado separadamente. Verificar resultado e custo real antes de qualquer conclusão.

## Critério estrito de erro de memória

Uma mensagem genérica como `The visual has exceeded the available resources` não confirma, sozinha, que o limite atingido foi **memória**. Pode faltar a identificação do recurso. Para classificar o cenário anual como falta de memória, registrar a mensagem literal detalhada contendo `memory` ou `memória`, vinculada ao visual/execução. O código `0xC13E0003`, isolado, é tratado como **diagnóstico pendente**, pois pode surgir na atualização do modelo, que é um fluxo diferente. Erros de autenticação, timeout e outros limites não aprovam o teste de memória.

O avaliador marca no máximo `CANDIDATOS_PARA_READBACK`; exige-se leitura independente do relatório no Service para verificar o efeito real da alteração. Referências: [limites de consultas visuais](https://learn.microsoft.com/pt-br/power-bi/create-reports/desktop-set-visual-query-limits) e [solução de problemas de atualização](https://learn.microsoft.com/pt-br/power-bi/connect-data/refresh-troubleshooting-refresh-scenarios).

## Limitações
- A view calcula datas sintéticas: folding pode existir mesmo sem índice/seletividade na fonte. Verificar plano/IO.
- Não há conexão com SQL/Service nesta entrega. Todos os CSVs começam em PENDENTE.
- O avaliador não autentica as evidências externas e não executa Power BI nem SQL Server.

## Fontes
- https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure
- https://learn.microsoft.com/pt-br/power-bi/create-reports/desktop-set-visual-query-limits
- https://learn.microsoft.com/en-us/power-bi/create-reports/performance-analyzer
- https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure

Regras: chatgpt-operational-rules/main@58dcd4200f412a866278027ba9e433439a03f3b3. Base: powerbi-platform/main@bc2285c15b54bbef0be20be3ddb8c41160a279e8. Issue #31 (não duplicar #29, painel-powerbi #27).
