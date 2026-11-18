// Alternativa quando a origem armazena DataKey inteira AAAAMMDD.
// Requer RangeStart e RangeEnd exatamente à meia-noite.
// Caso as datas incluam hora, use a coluna datetime nativa para evitar perda.
let
    ChaveData = (data as datetime) as number =>
        Date.Year(DateTime.Date(data)) * 10000 +
        Date.Month(DateTime.Date(data)) * 100 +
        Date.Day(DateTime.Date(data)),
    Inicio = ChaveData(RangeStart),
    Fim = ChaveData(RangeEnd),
    Fonte = Sql.Database(ServidorSql, BancoSql, [CreateNavigationProperties = false]),
    Tabela = Fonte{[Schema = "dbo", Item = "FatoMovimento"]}[Data],
    LinhasDoPeriodo = Table.SelectRows(
        Tabela,
        each [DataKey] >= Inicio and [DataKey] < Fim
    )
in
    LinhasDoPeriodo
