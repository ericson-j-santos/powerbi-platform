/* Somente leitura: estatísticas SQL reais por período.
   Data da VIEW é calculada e pode exigir trabalho antes do filtro;
   query folding NÃO garante leitura seletiva na origem. */
USE [AdventureWorksDW2022];
GO
SET NOCOUNT ON;
IF COL_LENGTH(N'dbo.vw_LabPBI_Memoria_2026', N'ReplicaID') IS NULL
    THROW 51020, 'VIEW ausente ou incompatível.', 1;
DECLARE @QtdeReplicas int = 1;
IF @QtdeReplicas NOT IN (1,10,40,80)
    THROW 51021, 'Replicas fora da escala autorizada.', 1;
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
SELECT COUNT_BIG(*) AS LinhasJan,
       SUM(CONVERT(decimal(38,4), ValorVenda)) AS VendasJan
FROM dbo.vw_LabPBI_Memoria_2026
WHERE ReplicaID >= 0 AND ReplicaID < @QtdeReplicas
  AND DataMovimento >= '20260101' AND DataMovimento < '20260201';
SELECT COUNT_BIG(*) AS LinhasAno,
       SUM(CONVERT(decimal(38,4), ValorVenda)) AS VendasAno
FROM dbo.vw_LabPBI_Memoria_2026
WHERE ReplicaID >= 0 AND ReplicaID < @QtdeReplicas
  AND DataMovimento >= '20260101' AND DataMovimento < '20270101';
SET STATISTICS IO OFF;
SET STATISTICS TIME OFF;
GO
