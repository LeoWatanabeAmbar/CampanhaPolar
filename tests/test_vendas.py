from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.adiantamento import DataAccessError
from polar.vendas import (
    LOAD_FUNCTION,
    SEPTEMBER,
    SalesRepository,
    calculate_region_results,
    sales_xp,
    working_days,
)


def sample_rows():
    return [
        {
            "data_referencia": "2026-09-15",
            "regiao": "REG 01",
            "time": "TIME SUL",
            "meta": 210000,
            "realizado": 100000,
            "vendedores": "Vendedor A · Vendedor B",
        },
        {
            "data_referencia": "2026-09-15",
            "regiao": "REG 02",
            "time": "CANAIS",
            "meta": 105000,
            "realizado": 40000,
            "vendedores": "Vendedor C",
        },
    ]


class FakeRequest:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def rpc(self, function, parameters):
        self.calls.append((function, parameters))
        return FakeRequest(self.data)


def test_september_working_days_include_reference_and_exclude_national_holiday():
    assert working_days(SEPTEMBER, date(2026, 9, 14)) == (21, 9, 12)
    assert working_days(SEPTEMBER, date(2026, 9, 15)) == (21, 10, 11)


@pytest.mark.parametrize(
    ("percentage", "expected"),
    [
        (Decimal("59.999"), 0),
        (Decimal("60"), 100),
        (Decimal("70"), 200),
        (Decimal("80"), 350),
        (Decimal("90"), 450),
        (Decimal("100"), 500),
        (Decimal("109.999"), 500),
        (Decimal("110"), 550),
        (Decimal("120"), 600),
        (Decimal("130"), 650),
        (Decimal("139.999"), 650),
        (Decimal("140"), 700),
        (Decimal("150"), 750),
    ],
)
def test_sales_xp_uses_exact_confirmed_boundaries(percentage, expected):
    assert sales_xp(percentage) == expected


def test_calculation_uses_partial_goal_and_keeps_one_result_per_region():
    rows = [sample_rows()[0]]
    results = calculate_region_results(rows, SEPTEMBER, date(2026, 9, 15))

    assert len(results) == 1
    result = results[0]
    assert result["vendedores"] == "Vendedor A · Vendedor B"
    assert result["meta_diaria"] == Decimal("10000")
    assert result["meta_parcial"] == Decimal("100000")
    assert result["atingimento_parcial_pct"] == Decimal("100")
    assert result["xp"] == 500
    assert result["dias_uteis_restantes"] == 11
    assert result["necessario_dia_util_restante"] == Decimal("10000")


def test_example_at_110_percent_scores_550_xp():
    rows = [{**sample_rows()[0], "data_referencia": "2026-09-14", "realizado": 99000}]
    result = calculate_region_results(rows, SEPTEMBER)[0]

    assert result["meta_parcial"] == Decimal("90000")
    assert result["atingimento_parcial_pct"] == Decimal("110")
    assert result["xp"] == 550


def test_repository_loads_september_regional_sales():
    client = FakeClient(sample_rows())
    rows = SalesRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": "2026-09-01"})]
    assert rows[0]["regiao"] == "REG 01"
    assert rows[0]["meta"] == Decimal("210000")
    assert rows[0]["realizado"] == Decimal("100000")


def test_repository_explains_outdated_rpc_contract():
    client = FakeClient([{"regiao": "REG 01"}])
    with pytest.raises(DataAccessError, match="vendas_quadrimestre.sql"):
        SalesRepository(client).load()


def test_sql_applies_sales_eligibility_and_regional_goal_rules():
    sql = Path("sql/vendas_quadrimestre.sql").read_text(encoding="utf-8").lower()

    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "set statement_timeout = '60s'" in sql
    assert "at time zone 'america/sao_paulo'" in sql
    assert "m.meta > 0" in sql
    assert "f.is_item_valido_metricas is true" in sql
    assert "f.is_venda_comercial is true" in sql
    assert "vw_clientes_inadimplentes" in sql
    assert "fct_faturamento_item" in sql
    assert "fct_nota_devolucao" in sql
    assert "valor_devolucao_alocado" in sql
    assert "greatest(" in sql
    assert "group by vd.regiao" in sql
    assert "grant execute on function public.campanha_polar_carregar_vendas_regionais(date)" in sql


def page_runner():
    import streamlit as st
    from app import render_quadrimester_sales

    render_quadrimester_sales(st.session_state["repo"])


def test_page_shows_partial_goal_attainment_and_xp_by_region():
    repository = SimpleNamespace(load=lambda month: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert len(app.metric) == 4
    assert app.metric[0].label == "Meta de setembro"
    assert app.metric[1].label == "Meta parcial até hoje"
    assert app.metric[2].label == "Realizado até hoje"
    assert app.metric[3].label == "Atingimento da meta parcial"
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert list(table.columns) == [
        "Região", "Vendedores", "Realizado", "Meta parcial", "Atingimento parcial",
        "XP da região", "Meta mensal", "Meta diária", "Dias úteis", "Saldo da meta",
        "Necessário/dia restante",
    ]
    assert list(table["XP da região"]) == [500, 350]
    assert list(table["Dias úteis"]) == ["10 de 21", "10 de 21"]
