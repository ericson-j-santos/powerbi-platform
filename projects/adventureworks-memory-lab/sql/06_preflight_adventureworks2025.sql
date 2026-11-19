/* Apenas leitura, sem USE/CREATE/ALTER/DROP.
   Verifica origem OLTP AdventureWorks2025, opção para instância existente.
   Execute integralmente, em sessão SQL LAB autorizada, começando por aqui.
*/
SET NOCOUNT ON;
DECLARE @BancoID int = DB_ID(N'AdventureWorks2025');
DECLARE @DetalheID int = OBJECT_ID(N'AdventureWorks2025.Sales.SalesOrderDetail', N'U');
DECLARE @CabecalhoID int = OBJECT_ID(N'AdventureWorks2025.Sales.SalesOrderHeader', N'U');

SELECT @@SERVERNAME AS ServidorSQL,
       @BancoID AS BancoID,
       @DetalheID AS TabelaDetalheID,
       @CabecalhoID AS TabelaCabecalhoID,
       CASE WHEN @BancoID IS NULL THEN N'BLOQUEADO_BANCO_AUSENTE'
            WHEN @DetalheID IS NULL OR @CabecalhoID IS NULL
                 THEN N'BLOQUEADO_TABELA_AUSENTE_OU_SEM_VISIBILIDADE'
            ELSE N'ESTRUTURA_VISIVEL_TESTAR_SELECT' END AS Estado;

IF @BancoID IS NULL OR @DetalheID IS NULL OR @CabecalhoID IS NULL
BEGIN
    PRINT N'PREFLIGHT_BLOQUEADO_SEM_LEITURA_DA_FONTE';
    RETURN;
END;

/* A consulta só é compilada/executada quando ambas as tabelas existem.
   É necessário SELECT em ambas. Não consulta qualquer banco SIIAC. */
EXEC sys.sp_executesql N'
SELECT COUNT_BIG(*) AS LinhasOrigem,
       COUNT_BIG(*) * CONVERT(bigint,40) AS LinhasCom40Replicas,
       COUNT_BIG(*) * CONVERT(bigint,80) AS LinhasCom80Replicas,
       SUM(CONVERT(decimal(38,4),CONVERT(decimal(19,4),d.LineTotal)))
           AS ValorOrigemArredondadoPorLinha,
       SUM(CONVERT(bigint,d.OrderQty)) AS ItensOrigem
FROM [AdventureWorks2025].[Sales].[SalesOrderDetail] AS d
JOIN [AdventureWorks2025].[Sales].[SalesOrderHeader] AS h
  ON d.SalesOrderID = h.SalesOrderID;';
