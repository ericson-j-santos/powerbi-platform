/* Somente leitura. Escalonamento: 1, 10, 40 ou 80 conforme os testes autorizados.
   Evita COUNT DISTINCT de milhões de textos. */
USE [AdventureWorksDW2022];
GO
SET NOCOUNT ON;
IF OBJECT_ID(N'dbo.vw_LabPBI_Memoria_2026', N'V') IS NULL
    THROW 51010, 'VIEW de laboratorio nao encontrada.', 1;
IF COL_LENGTH(N'dbo.vw_LabPBI_Memoria_2026', N'ReplicaID') IS NULL
    THROW 51011, 'VIEW existe sem ReplicaID. Inspecione equivalencia.', 1;

DECLARE @QtdeReplicas int = 1;
IF @QtdeReplicas NOT IN (1, 10, 40, 80)
    THROW 51012, 'Escolha 1, 10, 40 ou 80 replicas.', 1;

SELECT
    @QtdeReplicas AS Replicas, COUNT_BIG(*) AS LinhasObtidas,
    MIN(DataMovimento) AS MenorData, MAX(DataMovimento) AS MaiorData,
    SUM(CONVERT(decimal(38,4), ValorVenda)) AS VendasObtidas,
    SUM(CONVERT(bigint, Quantidade)) AS ItensObtidos
FROM dbo.vw_LabPBI_Memoria_2026
WHERE ReplicaID >= 0 AND ReplicaID < @QtdeReplicas
  AND DataMovimento >= '20260101' AND DataMovimento < '20270101';

SELECT
    COUNT_BIG(*) * CONVERT(bigint,@QtdeReplicas) AS LinhasEsperadas,
    SUM(CONVERT(decimal(38,4), SalesAmount)) * @QtdeReplicas AS VendasEsperadas,
    SUM(CONVERT(bigint, OrderQuantity)) * @QtdeReplicas AS ItensEsperados
FROM dbo.FactInternetSales;
GO
