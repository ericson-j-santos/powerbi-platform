"""Validação estática de contratos M e DAX. Não substitui Power BI Desktop."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContratosPowerBI(unittest.TestCase):
    def test_filtro_datetime_sem_sobrepor_particoes(self):
        texto = (ROOT / "shared/power-query/incremental_sqlserver_datetime.m").read_text(encoding="utf-8")
        self.assertIn("[DataMovimento] >= RangeStart", texto)
        self.assertIn("[DataMovimento] < RangeEnd", texto)
        self.assertNotIn("[DataMovimento] <= RangeEnd", texto)
        self.assertNotIn("Table.Buffer(", texto)
        self.assertIn("Table.SelectRows(", texto)
        self.assertIn("Sql.Database(", texto)

    def test_filtro_chave_inteira(self):
        texto = (ROOT / "shared/power-query/incremental_sqlserver_chave_aaaammdd.m").read_text(encoding="utf-8")
        self.assertIn("[DataKey] >= Inicio", texto)
        self.assertIn("[DataKey] < Fim", texto)
        self.assertIn("ChaveData(RangeStart)", texto)
        self.assertIn("ChaveData(RangeEnd)", texto)

    def test_dax_nao_finge_salvar_checkpoint(self):
        texto = (ROOT / "shared/dax/incremental_analise.dax").read_text(encoding="utf-8")
        for termo in ("DEFINE", "MEASURE FatoMovimento[Valor Total]",
                      "CALCULATE(", "DATEADD(", "DIVIDE(", "EVALUATE", "SUMMARIZECOLUMNS("):
            self.assertIn(termo, texto)
        self.assertNotIn("DEFINE TABLE", texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
