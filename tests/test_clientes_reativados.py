from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.clientes_reativados import LOAD_FUNCTION, ReactivatedCustomersRepository

MONTH = date(2026, 9, 1)


def sample_rows():
    return [
        {
            "grupo_comercial_id": "E672",
            "nome_grupo_comercial": "GELLAR",
            "data_reativacao": "2026-09-02",
            "data_ultima_compra": "2025-10-07",
            "prazo_meses": 6,
            "pedidos": "01101/058476",
            "vendedor": "Vendedor A",
            "regiao": "CANAIS 01",
            "segmento": "Canais",
            "situacao_atribuicao": "Integral",
            "xp": 8,
        },
        {
            "grupo_comercial_id": "CB2",
            "nome_grupo_comercial": "URBEN PARTICIPAÇÕES",
            "data_reativacao": "2026-09-04",
            "data_ultima_compra": "2025-05-08",
            "prazo_meses": 12,
            "pedidos": "01101/058578",
            "vendedor": "Vendedor B",
            "regiao": "NORTE 01",
            "segmento": "Construção",
            "situacao_atribuicao": "Divisão 50/50",
            "xp": 4,
        },
        {
            "grupo_comercial_id": "CB2",
            "nome_grupo_comercial": "URBEN PARTICIPAÇÕES",
            "data_reativacao": "2026-09-04",
            "data_ultima_compra": "2025-05-08",
            "prazo_meses": 12,
            "pedidos": "01101/058578",
            "vendedor": "Vendedor C",
            "regiao": "NORTE 02",
            "segmento": "Construção",
            "situacao_atribuicao": "Divisão 50/50",
            "xp": 4,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO PENDENTE",
            "data_reativacao": "2026-09-12",
            "data_ultima_compra": "2025-01-01",
            "prazo_meses": 12,
            "pedidos": "01101/058999",
            "vendedor": "Vendedor D",
            "regiao": "NORTE 01",
            "segmento": "Construção",
            "situacao_atribuicao": "Pendente: região sem meta",
            "xp": 0,
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


def test_repository_loads_whole_campaign():
    client = FakeClient(sample_rows())
    rows = ReactivatedCustomersRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": None})]
    assert rows[0]["prazo_meses"] == 6
    assert rows[1]["xp"] == 4


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        ReactivatedCustomersRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_sql_applies_reactivation_rules():
    sql = Path("sql/clientes_reativados.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "set statement_timeout = '60s'" in sql
    assert "#variable_conflict use_column" in sql
    assert "grant execute on function public.campanha_polar_carregar_clientes_reativados(date)" in sql
    assert "interval '6 months'" in sql
    assert "interval '12 months'" in sql
    assert "lag(e.data_emissao)" in sql
    assert "then 8.0 / r.quantidade_vendedores" in sql
    assert "detalhes as (" in sql
    assert "inner join detalhes as d" in sql
    assert "vw_clientes_inadimplentes" in sql
    assert "fct_nota_devolucao" in sql


def page_runner():
    import streamlit as st
    from app import render_reactivated_customers

    render_reactivated_customers(st.session_state["repo"])


def test_page_renders_reactivated_summary_region_filter_and_details():
    repository = SimpleNamespace(load=lambda: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert len(app.metric) == 0
    assert len(app.selectbox) == 1
    assert app.selectbox[0].label == "Região"
    assert len(app.dataframe) == 2
    assert list(app.dataframe[0].value.columns) == [
        "Região",
        "Quantidade de clientes reativados",
        "Lista dos clientes reativados",
        "Total XP",
    ]
    detail = app.dataframe[1].value
    assert list(detail.columns) == [
        "Data", "Última compra", "Prazo", "Grupo comercial", "Pedido de venda",
        "Vendedores", "Região", "Segmento", "Atribuição", "XP",
    ]
    triangulation = detail[detail["Grupo comercial"] == "URBEN PARTICIPAÇÕES"]
    assert list(triangulation["Vendedores"]) == ["Vendedor B", "Vendedor C"]
    assert list(triangulation["Região"]) == ["NORTE 01", "NORTE 02"]
    assert list(triangulation["XP"]) == [4.0, 4.0]


def test_reactivated_region_summary_counts_event_once_and_sums_xp():
    import pandas as pd

    from app import build_reactivated_customers_region_summary

    summary = build_reactivated_customers_region_summary(
        pd.DataFrame(sample_rows())
    ).set_index("Região")

    assert summary.loc["CANAIS 01", "Quantidade de clientes reativados"] == 1
    assert summary.loc["CANAIS 01", "Total XP"] == pytest.approx(8)
    assert summary.loc["NORTE 01", "Quantidade de clientes reativados"] == 2
    assert summary.loc["NORTE 01", "Lista dos clientes reativados"].splitlines() == [
        "GRUPO PENDENTE", "URBEN PARTICIPAÇÕES",
    ]
    assert summary.loc["NORTE 01", "Total XP"] == pytest.approx(4)
    assert summary.loc["NORTE 02", "Quantidade de clientes reativados"] == 1
    assert summary.loc["NORTE 02", "Total XP"] == pytest.approx(4)
