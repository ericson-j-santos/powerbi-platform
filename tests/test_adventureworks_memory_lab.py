"""Testes locais do LAB AdventureWorks, sem SQL Server nem Power BI Service."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / "projects" / "adventureworks-memory-lab"
sys.path.insert(0, str(ROOT / "tools"))
from avaliar_cenarios import analisar, carregar


def caso(cenario, filtro, resultado, *, erro="", linhas="42",
         vendas="100.00", itens="84", ambiente="Desktop", run="run"):
    return {
        "cenario": cenario, "filtro": filtro, "resultado": resultado,
        "replicas": "1", "ambiente": ambiente, "erro_literal": erro,
        "evidencia": "TESTE_SINTETICO_LOCAL", "workspace_id": "lab",
        "modelo_id": "modelo", "run_id": run,
        "sql_linhas": linhas, "dax_linhas": linhas,
        "sql_vendas": vendas, "dax_vendas": vendas,
        "sql_itens": itens, "dax_itens": itens,
    }


def cenarios(ambiente="Desktop"):
    return [
        caso("A_base", "2026-01", "sucesso", linhas="4",
             vendas="10.00", itens="8", ambiente=ambiente, run="mes"),
        caso("A_base", "2026", "falha", erro="Query memory limit exceeded",
             ambiente=ambiente, run="ano"),
        caso("B_visual_agregado", "2026", "sucesso",
             ambiente=ambiente, run="corrigido"),
    ]


class TesteAdventureWorksMemoria(unittest.TestCase):
    def test_candidato_nao_equivale_a_homologacao(self):
        resposta = analisar(cenarios())
        self.assertEqual(resposta["estado"], "CANDIDATOS_PARA_READBACK")
        self.assertEqual(resposta["correcoes"][0]["estado"], "CANDIDATO_NAO_HOMOLOGADO")

    def test_service_runs_distintos(self):
        self.assertEqual(analisar(cenarios("Service"))["estado"], "CANDIDATOS_PARA_READBACK")

    def test_service_run_repetido_falha_fechado(self):
        a = cenarios("Service")
        a[1]["run_id"] = a[0]["run_id"]
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_service_workspace_divergente_falha_fechado(self):
        a = cenarios("Service")
        a[2]["workspace_id"] = "outro"
        self.assertEqual(analisar(a)["estado"], "BASELINE_RELATADA")

    def test_sem_medicoes_reais(self):
        rows = carregar(ROOT / "evidencias" / "MATRIZ_DE_TESTES.csv")
        self.assertEqual(analisar(rows)["estado"], "SEM_EVIDENCIA")

    def test_erro_de_credencial_nao_e_erro_de_memoria(self):
        a = cenarios()
        a[1]["erro_literal"] = "Invalid credentials"
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_recurso_generico_nao_comprova_memoria(self):
        a = cenarios()
        a[1]["erro_literal"] = "The query has exceeded the available resources."
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_codigo_refresh_isolado_nao_comprova_memoria_visual(self):
        a = cenarios()
        a[1]["erro_literal"] = "0xC13E0003"
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_memoria_explicitamente_identificada(self):
        a = cenarios()
        a[1]["erro_literal"] = "Limite de memória excedido"
        self.assertEqual(analisar(a)["estado"], "CANDIDATOS_PARA_READBACK")

    def test_correcao_com_linhas_perdidas_bloqueia(self):
        a = cenarios()
        a[2]["sql_linhas"] = "0"
        a[2]["dax_linhas"] = "0"
        resposta = analisar(a)
        self.assertEqual(resposta["estado"], "BASELINE_RELATADA")
        self.assertEqual(resposta["pendencias"][0]["motivo"], "divergencia_baseline_anual_linhas")

    def test_ano_sem_origem_sql_bloqueia(self):
        a = cenarios()
        a[1]["sql_linhas"] = ""
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_ano_zerado_bloqueia(self):
        a = cenarios()
        for f in ("sql_linhas", "sql_vendas", "sql_itens"):
            a[1][f] = "0"
        self.assertEqual(analisar(a)["estado"], "INSUFICIENTE")

    def test_nan_bloqueia(self):
        a = cenarios()
        a[2]["dax_vendas"] = "NaN"
        self.assertEqual(analisar(a)["estado"], "BASELINE_RELATADA")

    def test_sql_fracionario_bloqueia(self):
        a = cenarios()
        a[2]["sql_linhas"] = "42.5"
        self.assertEqual(analisar(a)["estado"], "BASELINE_RELATADA")

    def test_dax_divergente_bloqueia(self):
        a = cenarios()
        a[2]["dax_vendas"] = "99.99"
        self.assertEqual(analisar(a)["estado"], "BASELINE_RELATADA")

    def test_duplicidade_bloqueia(self):
        a = cenarios()
        a.append(dict(a[0]))
        self.assertEqual(analisar(a)["estado"], "BLOQUEADO")

    def test_mesmo_csv_duas_leituras_identicas(self):
        a = cenarios()
        self.assertEqual(analisar(a), analisar(a))

    def test_preflight_somente_conta_se_banco_existe(self):
        sql = (ROOT / "sql" / "01_preflight.sql").read_text(encoding="utf-8")
        self.assertIn("IF @BancoExiste IS NULL OR @TabelaExiste IS NULL", sql)
        self.assertLess(sql.index("IF @BancoExiste IS NULL"),
                        sql.index("EXEC sys.sp_executesql"))

    def test_view_bloqueia_duplicidade(self):
        sql = (ROOT / "sql" / "02_criar_view.sql").read_text(encoding="utf-8")
        self.assertIn("IF OBJECT_ID(N'dbo.vw_LabPBI_Memoria_2026') IS NOT NULL", sql)
        self.assertIn("CREATE VIEW", sql)
        self.assertNotIn("DROP VIEW", sql.upper())

    def test_select_sem_view_so_leitura_e_parametrizado(self):
        m = (ROOT / "powerquery" / "04_sem_view_somente_leitura.pq").read_text(encoding="utf-8")
        codigo = "\n".join(
            linha for linha in m.splitlines()
            if not linha.strip().startswith("//")
        )
        self.assertIn("Value.NativeQuery(", codigo)
        self.assertIn("[QtdeReplicas = Escala]", codigo)
        self.assertIn("[EnableFolding = true]", codigo)
        self.assertIn("FROM dbo.FactInternetSales AS f", codigo)
        self.assertIn("CROSS JOIN", codigo)
        self.assertIn("r.ReplicaID < @QtdeReplicas", codigo)
        self.assertIn("CHECKSUM(", codigo)
        self.assertIn("20260101", codigo)
        self.assertIn("80", codigo)
        self.assertNotIn("Table.Buffer", codigo)
        import re
        self.assertNotRegex(codigo.upper(), r"\b(?:CREATE|ALTER|DROP|TRUNCATE|DELETE|INSERT|UPDATE)\s+\w+\b")

    def test_sql_sem_view_controle_independente(self):
        sql = (ROOT / "sql" / "05_validar_sem_view.sql").read_text(encoding="utf-8")
        comando = "\n".join(
            linha for linha in sql.splitlines()
            if not linha.strip().startswith("--") and not linha.strip().startswith("/*")
        )
        self.assertIn("dbo.FactInternetSales", comando)
        self.assertIn("CROSS APPLY", comando)
        self.assertIn("LinhasJaneiro", comando)
        self.assertIn("VendasEsperadasAno", comando)
        self.assertIn("r.ReplicaID < @QtdeReplicas", comando)
        self.assertIn("IF @QtdeReplicas NOT IN (1, 10, 40, 80)", comando)
        self.assertNotIn("CREATE VIEW", comando.upper())
        import re
        self.assertNotRegex(comando.upper(), r"\b(?:CREATE|ALTER|DROP|TRUNCATE|DELETE|INSERT|UPDATE)\s+\w+\b")

    def test_detector_dml_ddl_falha_em_alteracao_de_esquema(self):
        import re
        proibido = re.compile(r"\b(?:CREATE|ALTER|DROP|TRUNCATE|DELETE|INSERT|UPDATE)\s+\w+\b")
        self.assertRegex("CREATE VIEW dbo.Tabela", proibido)
        self.assertRegex("DELETE FROM dbo.Tabela", proibido)
        self.assertRegex("DROP TABLE dbo.Tabela", proibido)
        self.assertNotRegex("SELECT * FROM dbo.Tabela", proibido)

    def test_readme_prefere_rota_sem_ddl(self):
        txt = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Procedimento — rota recomendada sem DDL", txt)
        self.assertIn("sql/05_validar_sem_view.sql", txt)
        self.assertIn("powerquery/04_sem_view_somente_leitura.pq", txt)
        self.assertIn("folding não é garantido", txt)

    def test_incremental_filtro_meio_aberto(self):
        m = (ROOT / "powerquery" / "03_incremental.pq").read_text(encoding="utf-8")
        self.assertIn("[DataMovimento] >= RangeStart", m)
        self.assertIn("[DataMovimento] < RangeEnd", m)
        self.assertNotIn("Table.Buffer", m)

    def test_otimizacao_remove_texto_alta_cardinalidade(self):
        base = (ROOT / "powerquery" / "01_base.pq").read_text(encoding="utf-8")
        otim = (ROOT / "powerquery" / "02_otimizado.pq").read_text(encoding="utf-8")
        self.assertIn("ObservacaoDetalhada", base)
        self.assertNotIn("ObservacaoDetalhada", otim)
        self.assertNotIn("LinhaUnica", otim)


if __name__ == "__main__":
    unittest.main()
