// Modelo genérico Power Query M para atualização incremental no Power BI.
// Criar parâmetros RangeStart e RangeEnd do tipo Data/Hora.
// Ajustar ServidorSql, BancoSql, dbo.FatoMovimento e DataMovimento.
// Não usar Table.Buffer antes do filtro; verificar query folding.
// DataMovimento é a chave de partição; DataAlteracao pode ser configurada
// separadamente em "Detectar alterações nos dados" (quando aplicável).
let
    Fonte = Sql.Database(ServidorSql, BancoSql, [CreateNavigationProperties = false]),
    Tabela = Fonte{[Schema = "dbo", Item = "FatoMovimento"]}[Data],
    LinhasDoPeriodo = Table.SelectRows(
        Tabela,
        each [DataMovimento] >= RangeStart
          and [DataMovimento] < RangeEnd
    ),
    ColunasNecessarias = Table.SelectColumns(
        LinhasDoPeriodo,
        {"IdMovimento", "DataMovimento", "DataAlteracao", "Valor"}
    )
in
    ColunasNecessarias
