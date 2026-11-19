// Rota alternativa: AdventureWorks2025 OLTP, somente SELECT, sem CREATE VIEW.
// Origem candidata existente no Noteri; verificar preflight/identidade antes.
// Consulta FatoLaboratorio em PBIX de LAB NOVO; não usar o modelo SIIAC.
// QtdeReplicas: parâmetro inteiro = 1 inicialmente, permitido {1,10,40,80}.
// ValorVenda usa 4 casas por linha (LineTotal); compara SQL 07, não TotalDue.
// EnableFolding = true não comprova folding nem acesso físico; medir SQL real.
let
    Escala = if List.Contains({1, 10, 40, 80}, QtdeReplicas)
        then QtdeReplicas
        else error "QtdeReplicas deve ser 1, 10, 40 ou 80",
    Fonte = Sql.Database(
        "SERVIDOR_SQL_LAB", "AdventureWorks2025",
        [CreateNavigationProperties = false]
    ),
    Fato = Value.NativeQuery(
        Fonte,
        "
SELECT
    CONVERT(datetime2(0), DATEADD(DAY,
        CONVERT(int, ABS(CONVERT(bigint, CHECKSUM(
            d.SalesOrderID, d.SalesOrderDetailID, r.ReplicaID))) % 365),
        CONVERT(datetime2(0), '20260101', 112))) AS DataMovimento,
    CONCAT(d.SalesOrderID, '-', d.SalesOrderDetailID,
           '-', r.ReplicaID) AS LinhaUnica,
    r.ReplicaID AS ReplicaID,
    d.ProductID AS ProdutoID,
    h.CustomerID AS ClienteID,
    d.OrderQty AS Quantidade,
    CONVERT(decimal(19,4), d.LineTotal) AS ValorVenda,
    CONCAT('AdventureWorks OLTP | Pedido ', d.SalesOrderID,
           ' / Item ', d.SalesOrderDetailID,
           ' / Replica ', r.ReplicaID,
           ' / Produto ', d.ProductID,
           ' / Cliente ', h.CustomerID) AS ObservacaoDetalhada
FROM Sales.SalesOrderDetail AS d
JOIN Sales.SalesOrderHeader AS h ON h.SalesOrderID = d.SalesOrderID
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
