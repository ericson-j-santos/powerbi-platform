"""Classificador somente leitura do protocolo Power BI LAB.

Não consulta SQL ou Power BI; só analisa medições registradas no CSV.
A saída NUNCA equivale à homologação do Service: exige readback externo.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUNAS = {
    "cenario", "filtro", "replicas", "resultado", "ambiente", "evidencia",
    "erro_literal", "sql_linhas", "sql_vendas", "sql_itens",
    "dax_linhas", "dax_vendas", "dax_itens", "workspace_id", "modelo_id", "run_id",
}
ERRO_MEMORIA = re.compile(
    r"mem[oó]ria|\bmemory\b|out.of.memory|resources? (?:has |have )?exceeded|"
    r"exceeded (?:the )?available resources|0xC13E0003",
    re.IGNORECASE,
)


def _total_sql(linha: dict) -> tuple[dict | None, str]:
    """Totais SQL da origem externa; nunca derivar os totais esperados do próprio DAX."""
    totais = {}
    for coluna in ("linhas", "vendas", "itens"):
        valor = (linha.get("sql_" + coluna) or "").strip()
        if not valor:
            return None, "falta_sql_" + coluna
        try:
            numero = Decimal(valor)
        except InvalidOperation:
            return None, "sql_nao_numerico_" + coluna
        if not numero.is_finite():
            return None, "sql_nao_finito_" + coluna
        if coluna in ("linhas", "itens") and numero != numero.to_integral_value():
            return None, "sql_nao_inteiro_" + coluna
        if numero < 0:
            return None, "sql_negativo_" + coluna
        totais[coluna] = numero
    return totais, "sql_valido"


def _numeros_consistentes(linha: dict, referencia: dict | None = None) -> tuple[bool, str]:
    totais, motivo = _total_sql(linha)
    if totais is None:
        return False, motivo
    for coluna, esperado in totais.items():
        valor = (linha.get("dax_" + coluna) or "").strip()
        if not valor:
            return False, "falta_dax_" + coluna
        try:
            obtido = Decimal(valor)
        except InvalidOperation:
            return False, "dax_nao_numerico_" + coluna
        if not obtido.is_finite():
            return False, "dax_nao_finito_" + coluna
        if obtido != esperado:
            return False, "divergencia_" + coluna
        if referencia is not None and esperado != referencia[coluna]:
            return False, "divergencia_baseline_anual_" + coluna
    return True, "totais_coincidem"


def analisar(linhas: list[dict]) -> dict:
    """Avalia A (mês/ano) e B/C (ano) sem afirmar E2E ou custo zero."""
    validas = []
    duplicadas = []
    chaves = set()
    for linha in linhas:
        if (linha.get("resultado") or "").strip().lower() not in ("sucesso", "falha"):
            continue
        chave = tuple((linha.get(c) or "").strip().lower() for c in
                      ("cenario", "filtro", "replicas", "ambiente"))
        if chave in chaves:
            duplicadas.append(chave)
        chaves.add(chave)
        validas.append({k: (v or "").strip() for k, v in linha.items() if k})
    if duplicadas:
        return {"estado": "BLOQUEADO", "motivo": "duplicidade_de_cenario", "duplicatas": len(duplicadas)}
    if not validas:
        return {"estado": "SEM_EVIDENCIA", "motivo": "nenhuma_execucao_registrada", "correcoes": []}

    def localizar(cenario, filtro, replicas, ambiente):
        return next((x for x in validas if x.get("cenario") == cenario
                     and x.get("filtro") == filtro
                     and x.get("replicas") == str(replicas)
                     and x.get("ambiente", "").casefold() == ambiente.casefold()), None)

    candidatos = []
    baselines = []
    pendencias = []
    for replica in (1, 10, 40, 80):
        for ambiente in ("Desktop", "Service"):
            mes = localizar("A_base", "2026-01", replica, ambiente)
            ano = localizar("A_base", "2026", replica, ambiente)
            if not (mes and ano):
                continue
            if not (mes.get("resultado") == "sucesso" and ano.get("resultado") == "falha"
                    and ERRO_MEMORIA.search(ano.get("erro_literal", ""))):
                continue
            identificadores = ("workspace_id", "modelo_id", "run_id") if ambiente == "Service" else ()
            if not all(mes.get(k) and ano.get(k) for k in ("evidencia", *identificadores)):
                pendencias.append({"replicas": replica, "ambiente": ambiente,
                                  "motivo": "evidencia_ou_identificador_ausente"})
                continue
            ok_mes, motivo_mes = _numeros_consistentes(mes)
            if not ok_mes:
                pendencias.append({"replicas": replica, "ambiente": ambiente,
                                  "motivo": "baseline_mes_" + motivo_mes})
                continue
            totais_ano, motivo_ano = _total_sql(ano)
            if totais_ano is None:
                pendencias.append({"replicas": replica, "ambiente": ambiente,
                                  "motivo": "baseline_ano_" + motivo_ano})
                continue
            totais_mes, _ = _total_sql(mes)
            if (totais_ano["linhas"] <= 0 or totais_ano["itens"] <= 0 or
                    totais_ano["vendas"] <= 0 or
                    any(totais_ano[k] < totais_mes[k] for k in totais_ano)):
                pendencias.append({"replicas": replica, "ambiente": ambiente,
                                  "motivo": "baseline_ano_sem_volume_ou_menor_que_mes"})
                continue
            if ambiente == "Service" and (
                mes["workspace_id"] != ano["workspace_id"] or
                mes["modelo_id"] != ano["modelo_id"] or
                mes["run_id"] == ano["run_id"]
            ):
                pendencias.append({"replicas": replica, "ambiente": ambiente,
                                  "motivo": "baseline_service_incompatível"})
                continue
            baselines.append({"replicas": replica, "ambiente": ambiente,
                              "estado": "baseline_relato_consistente"})
            for correcao in ("B_visual_agregado", "C_modelo_estreito"):
                atual = localizar(correcao, "2026", replica, ambiente)
                if not atual or atual.get("resultado") != "sucesso":
                    continue
                if not all(atual.get(k) for k in ("evidencia", *identificadores)):
                    pendencias.append({"cenario": correcao, "motivo": "evidencia_ausente"})
                    continue
                if ambiente == "Service" and (
                    atual["workspace_id"] != ano["workspace_id"] or
                    atual["run_id"] in (mes["run_id"], ano["run_id"])
                ):
                    pendencias.append({"cenario": correcao,
                                      "motivo": "service_workspace_ou_run_incompatível"})
                    continue
                ok, causa = _numeros_consistentes(atual, referencia=totais_ano)
                if not ok:
                    pendencias.append({"cenario": correcao, "motivo": causa})
                    continue
                candidatos.append({"correcao": correcao, "replicas": replica,
                                   "ambiente": ambiente,
                                   "estado": "CANDIDATO_NAO_HOMOLOGADO",
                                   "criterio": "mes_sucesso_ano_memoria_erro_ano_corrigido_sucesso_totais_SQL_DAX_iguais_a_origem"})
    return {
        "estado": ("CANDIDATOS_PARA_READBACK" if candidatos else
                   "BASELINE_RELATADA" if baselines else "INSUFICIENTE"),
        "baselines": baselines,
        "correcoes": candidatos,
        "pendencias": pendencias,
        "limite": "CSV nao verifica E2E, credenciais, custo zero, autenticidade nem leitura independente no Service",
    }


def carregar(caminho: Path) -> list[dict]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        faltantes = COLUNAS - set(leitor.fieldnames or [])
        if faltantes:
            raise ValueError("colunas_ausentes:" + ",".join(sorted(faltantes)))
        return list(leitor)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("arquivo", type=Path, help="CSV de evidencias local (somente leitura)")
    args = p.parse_args()
    try:
        saida = analisar(carregar(args.arquivo))
    except (ValueError, OSError, csv.Error) as exc:
        saida = {"estado": "BLOQUEADO", "motivo": str(exc)}
    print(json.dumps(saida, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()