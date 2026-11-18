// Power Query M — exemplo, não altera o modelo publicado.
// Crie parâmetros RangeStart e RangeEnd de tipo data/hora no Power BI Desktop.
// Os nomes precisam ser exatamente RangeStart e RangeEnd.
// Após a etapa abaixo, configure a política de atualização incremental no modelo.
// Confira se o filtro é executado NO SQL Server (query folding).
let
    Fonte = Sql.Database("SERVIDOR", "BANCO"),
    Tabela = Fonte{[Schema="dbo", Item="FatoMovimento"]}[Data],
    SomentePeriodo = Table.SelectRows(
        Tabela,
        each [DataAlteracao] >= RangeStart and [DataAlteracao] < RangeEnd
    )
in
    SomentePeriodo
