/* Validação independente da rota SELECT-only para AdventureWorks2025.
   NÃO altera tabelas, views, índices ou dados. Requer SELECT nas duas tabelas.
   Escalonar a variável 1 -> 10 -> 40 -> 80 somente com custo e limites OK.
*/
USE [AdventureWorks2025];
GO
SET NOCOUNT ON;
IF DB_NAME() <> N'AdventureWorks2025'
    THROW 51040, 'Banco inesperado, teste bloqueado', 1;
IF OBJECT_ID(N'Sales.SalesOrderDetail',N'U') IS NULL
   OR OBJECT_ID(N'Sales.SalesOrderHeader',N'U') IS NULL
    THROW 51041, 'Tabelas fonte ausentes ou sem visibilidade', 1;
DECLARE @QtdeReplicas int = 1;
IF @QtdeReplicas NOT IN (1,10,40,80)
    THROW 51042, 'Escala fora do contrato', 1;

/* Mesma regra de dados do Power Query; DataMovimento sintetizada em 2026.
   ValorVenda arredondado por linha a 4 casas, não equivale necessariamente
   ao TotalDue dos pedidos reais (frete/imposto não entram neste laboratório). */
SELECT @QtdeReplicas AS Replicas,
       COUNT_BIG(*) AS LinhasAno,
       SUM(CONVERT(decimal(38,4),CONVERT(decimal(19,4),d.LineTotal))) AS VendasAno,
       SUM(CONVERT(bigint,d.OrderQty)) AS ItensAno,
       SUM(CASE WHEN mov.DataMovimento >= '20260101'
                 AND mov.DataMovimento < '20260201'
                THEN CONVERT(bigint,1) ELSE CONVERT(bigint,0) END) AS LinhasJaneiro,
       SUM(CASE WHEN mov.DataMovimento >= '20260101'
                 AND mov.DataMovimento < '20260201'
                THEN CONVERT(decimal(38,4),CONVERT(decimal(19,4),d.LineTotal))
                ELSE CONVERT(decimal(38,4),0) END) AS VendasJaneiro,
       SUM(CASE WHEN mov.DataMovimento >= '20260101'
                 AND mov.DataMovimento < '20260201'
                THEN CONVERT(bigint,d.OrderQty)
                ELSE CONVERT(bigint,0) END) AS ItensJaneiro
FROM Sales.SalesOrderDetail AS d
JOIN Sales.SalesOrderHeader AS h ON h.SalesOrderID = d.SalesOrderID
CROSS JOIN (
    SELECT unidades.n + (10 * dezenas.n) AS ReplicaID
    FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS unidades(n)
    CROSS JOIN (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS dezenas(n)
) AS r
CROSS APPLY (VALUES(
    CONVERT(datetime2(0),DATEADD(DAY,
       CONVERT(int,ABS(CONVERT(bigint,CHECKSUM(
          d.SalesOrderID,d.SalesOrderDetailID,r.ReplicaID))) % 365),
       CONVERT(datetime2(0),'20260101',112)))
)) AS mov(DataMovimento)
WHERE r.ReplicaID >= 0 AND r.ReplicaID < @QtdeReplicas;

/* Segundo SELECT: controle independente sem CROSS JOIN ou datas sintéticas. */
SELECT @QtdeReplicas AS Replicas,
       COUNT_BIG(*) * CONVERT(bigint,@QtdeReplicas) AS LinhasEsperadasAno,
       SUM(CONVERT(decimal(38,4),CONVERT(decimal(19,4),d.LineTotal)))
           * @QtdeReplicas AS VendasEsperadasAno,
       SUM(CONVERT(bigint,d.OrderQty)) * @QtdeReplicas AS ItensEsperadosAno
FROM Sales.SalesOrderDetail AS d
JOIN Sales.SalesOrderHeader AS h ON h.SalesOrderID = d.SalesOrderID;
GO
