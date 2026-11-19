// Power Query M — cópia isolada do PBIX, removendo colunas de alta cardinalidade.
let
    Fonte = Sql.Database("SERVIDOR_SQL_LAB", "AdventureWorksDW2022", [CreateNavigationProperties = false]),
    Fato = Fonte{[Schema = "dbo", Item = "vw_LabPBI_Memoria_2026"]}[Data],
    ComReplica = Table.SelectRows(Fato, each [ReplicaID] >= 0 and [ReplicaID] < QtdeReplicas),
    Colunas = Table.SelectColumns(ComReplica, {
        "DataMovimento", "ProdutoID", "ClienteID", "Quantidade", "ValorVenda"
    }),
    Tipos = Table.TransformColumnTypes(Colunas, {
        {"DataMovimento", type datetime}, {"ProdutoID", Int64.Type},
        {"ClienteID", Int64.Type}, {"Quantidade", Int64.Type},
        {"ValorVenda", Currency.Type}
    })
in
    if QtdeReplicas = 1 or QtdeReplicas = 10 or QtdeReplicas = 40 or QtdeReplicas = 80
    then Tipos else error "QtdeReplicas deve ser 1, 10, 40 ou 80"
