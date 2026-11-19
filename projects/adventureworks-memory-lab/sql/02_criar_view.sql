/*
  LAB ISOLADO AdventureWorksDW2022 (2026).
  ÚNICA alteração: criar dbo.vw_LabPBI_Memoria_2026 se ainda não existir.
  Não cria tabela física e não modifica dados da origem.
  Expondo ReplicaID, permite variar carga de 1 a 80 sem recriar a view.
  Requer autorização específica do administrador do banco de LAB.
*/
USE [AdventureWorksDW2022];
GO
SET NOCOUNT ON;
IF DB_NAME() <> N'AdventureWorksDW2022'
    THROW 51000, 'Bloqueado: banco incorreto.', 1;
IF OBJECT_ID(N'dbo.FactInternetSales', N'U') IS NULL
    THROW 51001, 'Bloqueado: FactInternetSales nao encontrada.', 1;
IF OBJECT_ID(N'dbo.vw_LabPBI_Memoria_2026') IS NOT NULL
    THROW 51002, 'Bloqueado: objeto do laboratorio ja existe. Verifique sua definicao; nada foi alterado.', 1;

EXEC sys.sp_executesql N'
CREATE VIEW [dbo].[vw_LabPBI_Memoria_2026]
AS
WITH Digitos AS (
    SELECT d.n FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS d(n)
),
Replicas AS (
    SELECT u.n + (10 * d.n) AS ReplicaID
    FROM Digitos AS u CROSS JOIN Digitos AS d
)
SELECT
    CONVERT(datetime2(0), DATEADD(DAY,
        CONVERT(int, ABS(CONVERT(bigint, CHECKSUM(
            f.SalesOrderNumber, f.SalesOrderLineNumber, r.ReplicaID))) % 365),
        CONVERT(datetime2(0), ''20260101'', 112))) AS DataMovimento,
    CONCAT(f.SalesOrderNumber, ''-'', f.SalesOrderLineNumber,
           ''-'', r.ReplicaID) AS LinhaUnica,
    r.ReplicaID AS ReplicaID,
    f.ProductKey AS ProdutoID,
    f.CustomerKey AS ClienteID,
    f.OrderQuantity AS Quantidade,
    f.SalesAmount AS ValorVenda,
    CONCAT(''AdventureWorks DW | Pedido '', f.SalesOrderNumber,
           '' / Item '', f.SalesOrderLineNumber,
           '' / Replica '', r.ReplicaID,
           '' / Produto '', f.ProductKey,
           '' / Cliente '', f.CustomerKey) AS ObservacaoDetalhada
FROM dbo.FactInternetSales AS f
CROSS JOIN Replicas AS r
WHERE r.ReplicaID < 80;
';
PRINT 'VIEW CRIADA. Execute 03_validar.sql antes de carregar no Power BI.';
GO
