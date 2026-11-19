/* Apenas LAB AdventureWorksDW2022; nenhuma view/tabela criada ou modificada.
   Usa somente SELECT, gera réplicas virtuais e verifica janeir/2026 x ano/2026.
   Comece com @QtdeReplicas = 1. Aumente só após comprovar recursos/custo R$0.
   Altere apenas @QtdeReplicas para 1, 10, 40 ou 80.
*/
USE [AdventureWorksDW2022];
GO
SET NOCOUNT ON;
IF DB_NAME() <> N'AdventureWorksDW2022'
    THROW 51030, 'Banco SQL inesperado', 1;
IF OBJECT_ID(N'dbo.FactInternetSales', N'U') IS NULL
    THROW 51031, 'Tabela de origem ausente ou sem visibilidade', 1;
DECLARE @QtdeReplicas int = 1;
IF @QtdeReplicas NOT IN (1, 10, 40, 80)
    THROW 51032, 'Escala invalida; aceito apenas 1, 10, 40, 80', 1;

SELECT @QtdeReplicas AS Replicas,
       COUNT_BIG(*) AS LinhasAno,
       SUM(CONVERT(decimal(38,4), f.SalesAmount)) AS VendasAno,
       SUM(CONVERT(bigint, f.OrderQuantity)) AS ItensAno,
       SUM(CASE WHEN movimento.DataMovimento >= '20260101'
                 AND movimento.DataMovimento < '20260201'
                THEN CONVERT(bigint,1) ELSE CONVERT(bigint,0) END) AS LinhasJaneiro,
       SUM(CASE WHEN movimento.DataMovimento >= '20260101'
                 AND movimento.DataMovimento < '20260201'
                THEN CONVERT(decimal(38,4),f.SalesAmount)
                ELSE CONVERT(decimal(38,4),0) END) AS VendasJaneiro
FROM dbo.FactInternetSales AS f
CROSS JOIN (
    SELECT unidades.n + 10*dezenas.n AS ReplicaID
    FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS unidades(n)
    CROSS JOIN
         (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS dezenas(n)
) AS r
CROSS APPLY (VALUES(
    CONVERT(datetime2(0), DATEADD(DAY,
        CONVERT(int, ABS(CONVERT(bigint, CHECKSUM(
            f.SalesOrderNumber, f.SalesOrderLineNumber, r.ReplicaID))) % 365),
        CONVERT(datetime2(0), '20260101', 112)))
)) AS movimento(DataMovimento)
WHERE r.ReplicaID >= 0 AND r.ReplicaID < @QtdeReplicas;

-- Controle independente de totais: diretamente na tabela origem.
SELECT @QtdeReplicas AS Replicas,
       COUNT_BIG(*) * CONVERT(bigint,@QtdeReplicas) AS LinhasEsperadasAno,
       SUM(CONVERT(decimal(38,4),SalesAmount)) * @QtdeReplicas AS VendasEsperadasAno,
       SUM(CONVERT(bigint,OrderQuantity)) * @QtdeReplicas AS ItensEsperadosAno
FROM dbo.FactInternetSales;
GO
