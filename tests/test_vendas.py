from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.adiantamento import DataAccessError
from polar.vendas import (
    LOAD_FUNCTION,
    OCTOBER,
    SEPTEMBER,
    SalesRepository,
    calculate_cumulative_region_results,
    calculate_region_results,
    campaign_months_through,
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


def october_rows():
    return [
        {
            "data_referencia": "2026-10-15",
            "regiao": "REG 01",
            "time": "TIME SUL",
            "meta": 210000,
            "realizado": 90000,
            "vendedores": "Vendedor A",
        },
        {
            "data_referencia": "2026-10-15",
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


def test_campaign_months_accumulate_through_current_month():
    assert campaign_months_through(date(2026, 9, 15)) == (SEPTEMBER,)
    assert campaign_months_through(date(2026, 10, 15)) == (SEPTEMBER, OCTOBER)


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


def test_october_combines_full_september_with_partial_october():
    september = [
        {**sample_rows()[0], "data_referencia": "2026-09-30", "realizado": 220000},
        {**sample_rows()[1], "data_referencia": "2026-09-30", "realizado": 105000},
    ]
    results = calculate_cumulative_region_results(
        {SEPTEMBER: september, OCTOBER: october_rows()},
        date(2026, 10, 15),
    )

    first = results[0]
    assert first["regiao"] == "REG 01"
    assert first["metas_publicadas"] == Decimal("420000")
    assert first["meta_acumulada_ate_data"] == Decimal("310000")
    assert first["realizado_acumulado"] == Decimal("310000")
    assert first["atingimento_acumulado_pct"] == Decimal("100")
    assert first["xp"] == 500
    assert first["dias_uteis_decorridos"] == 10
    assert first["dias_uteis_restantes"] == 11


def test_repository_loads_september_regional_sales():
    client = FakeClient(sample_rows())
    rows = SalesRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": "2026-09-01"})]
    assert rows[0]["regiao"] == "REG 01"
    assert rows[0]["meta"] == Decimal("210000")
    assert rows[0]["realizado"] == Decimal("100000")


def test_repository_loads_all_elapsed_months_for_october():
    client = FakeClient(sample_rows())
    rows = SalesRepository(client).load_through(date(2026, 10, 15))

    assert list(rows) == [SEPTEMBER, OCTOBER]
    assert client.calls == [
        (LOAD_FUNCTION, {"p_competencia": "2026-09-01"}),
        (LOAD_FUNCTION, {"p_competencia": "2026-10-01"}),
    ]


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

    render_quadrimester_sales(
        st.session_state["repo"], st.session_state.get("reference")
    )


def test_page_shows_partial_goal_attainment_and_xp_by_region():
    repository = SimpleNamespace(load_through=lambda reference: {SEPTEMBER: sample_rows()})
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.session_state["reference"] = date(2026, 9, 15)
    app.run(timeout=15)

    assert not app.exception
    assert len(app.metric) == 5
    assert app.metric[0].label == "Metas publicadas até setembro"
    assert app.metric[1].label == "Meta acumulada até hoje"
    assert app.metric[2].label == "Realizado acumulado"
    assert app.metric[3].label == "Atingimento acumulado"
    assert app.metric[4].label == "Dias úteis"
    assert app.metric[4].value == "10 de 21"
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert list(table.columns) == [
        "Região", "Vendedores", "Realizado acumulado", "Meta acumulada até hoje",
        "Atingimento acumulado", "XP da região", "Meta diária atual",
    ]
    assert list(table["XP da região"]) == [500, 350]


def test_page_in_october_labels_and_displays_the_accumulated_quadrimester():
    september = [
        {**sample_rows()[0], "data_referencia": "2026-09-30", "realizado": 220000},
        {**sample_rows()[1], "data_referencia": "2026-09-30", "realizado": 105000},
    ]
    repository = SimpleNamespace(
        load_through=lambda reference: {SEPTEMBER: september, OCTOBER: october_rows()}
    )
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.session_state["reference"] = date(2026, 10, 15)
    app.run(timeout=15)

    assert not app.exception
    assert app.metric[0].label == "Metas publicadas até outubro"
    assert app.metric[1].label == "Meta acumulada até hoje"
    table = app.dataframe[0].value.set_index("Região")
    assert table.loc["REG 01", "Meta acumulada até hoje"] == pytest.approx(310000)
    assert table.loc["REG 01", "Realizado acumulado"] == pytest.approx(310000)
    assert table.loc["REG 01", "XP da região"] == 500
