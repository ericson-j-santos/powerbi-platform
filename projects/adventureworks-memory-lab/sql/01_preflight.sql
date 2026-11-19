/* AdventureWorksDW2022 — preflight somente leitura, execução integral segura.
   Alvo exclusivo: banco de laboratório. Não cria ou altera nenhum objeto. */
SET NOCOUNT ON;
DECLARE @Banco sysname = N'AdventureWorksDW2022';
DECLARE @BancoExiste int = DB_ID(@Banco);
DECLARE @TabelaExiste int = OBJECT_ID(N'AdventureWorksDW2022.dbo.FactInternetSales', N'U');
DECLARE @ViewExiste int = OBJECT_ID(N'AdventureWorksDW2022.dbo.vw_LabPBI_Memoria_2026', N'V');

SELECT @@SERVERNAME AS Servidor, DB_NAME() AS BancoAtual,
       @BancoExiste AS IdBancoAdventureWorksDW2022,
       @TabelaExiste AS IdTabelaOrigem, @ViewExiste AS IdViewLaboratorio,
       CASE WHEN @BancoExiste IS NULL THEN N'BLOQUEADO_BANCO_AUSENTE'
            WHEN @TabelaExiste IS NULL THEN N'BLOQUEADO_TABELA_AUSENTE_OU_SEM_PERMISSAO'
            ELSE N'PRECONDICOES_VALIDAS' END AS EstadoPreflight;

IF @BancoExiste IS NULL OR @TabelaExiste IS NULL
BEGIN
    PRINT N'PREFLIGHT_BLOQUEADO: confirme banco, instância e permissão SELECT.';
    RETURN;
END;
EXEC sys.sp_executesql N'
SELECT COUNT_BIG(*) AS LinhasOrigem,
       COUNT_BIG(*) * CONVERT(bigint, 80) AS LinhasEsperadasLaboratorio
FROM [AdventureWorksDW2022].[dbo].[FactInternetSales];';
