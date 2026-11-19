// AdventureWorksDW2022 LAB — somente SELECT, SEM CREATE VIEW e SEM alteração da origem.
// Colar como consulta FatoLaboratorio em PBIX novo; iniciar com QtdeReplicas=1.
// Criar parâmetro numérico inteiro QtdeReplicas = 1; permitir 1,10,40,80.
// Alterar SOMENTE SERVIDOR_SQL_LAB por uma instância SQL de laboratório autorizada.
// Value.NativeQuery aceita parâmetros separados; não concatenar SQL com entradas.
// Compatibilidade e query folding precisam ser confirmados no Desktop/SQL reais.
let
    Escala = if List.Contains({1, 10, 40, 80}, QtdeReplicas)
        then QtdeReplicas
        else error "QtdeReplicas deve ser 1, 10, 40 ou 80",
    Fonte = Sql.Database(
        "SERVIDOR_SQL_LAB", "AdventureWorksDW2022",
        [CreateNavigationProperties = false]
    ),
    Fato = Value.NativeQuery(
        Fonte,
        "
SELECT
    CONVERT(datetime2(0), DATEADD(DAY,
        CONVERT(int, ABS(CONVERT(bigint, CHECKSUM(
            f.SalesOrderNumber, f.SalesOrderLineNumber, r.ReplicaID))) % 365),
        CONVERT(datetime2(0), '20260101', 112))) AS DataMovimento,
    CONCAT(f.SalesOrderNumber, '-', f.SalesOrderLineNumber,
           '-', r.ReplicaID) AS LinhaUnica,
    r.ReplicaID AS ReplicaID,
    f.ProductKey AS ProdutoID,
    f.CustomerKey AS ClienteID,
    f.OrderQuantity AS Quantidade,
    f.SalesAmount AS ValorVenda,
    CONCAT('AdventureWorks DW | Pedido ', f.SalesOrderNumber,
           ' / Item ', f.SalesOrderLineNumber,
           ' / Replica ', r.ReplicaID,
           ' / Produto ', f.ProductKey,
           ' / Cliente ', f.CustomerKey) AS ObservacaoDetalhada
FROM dbo.FactInternetSales AS f
CROSS JOIN (
    SELECT unidades.n + (10 * dezenas.n) AS ReplicaID
    FROM (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS unidades(n)
    CROSS JOIN
         (VALUES (0),(1),(2),(3),(4),(5),(6),(7),(8),(9)) AS dezenas(n)
) AS r
WHERE r.ReplicaID >= 0 AND r.ReplicaID < @QtdeReplicas
        ",
        [QtdeReplicas = Escala],
        [EnableFolding = true]
    ),
    Colunas = Table.SelectColumns(Fato, {
        "DataMovimento", "LinhaUnica", "ProdutoID", "ClienteID",
        "Quantidade", "ValorVenda", "ObservacaoDetalhada"
    }),
    Tipos = Table.TransformColumnTypes(Colunas, {
        {"DataMovimento", type datetime}, {"LinhaUnica", type text},
        {"ProdutoID", Int64.Type}, {"ClienteID", Int64.Type},
        {"Quantidade", Int64.Type}, {"ValorVenda", Currency.Type},
        {"ObservacaoDetalhada", type text}
    })
in
    Tipos
