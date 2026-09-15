from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.clientes_novos import LOAD_FUNCTION, NewCustomersRepository

MONTH = date(2026, 9, 1)


def sample_rows():
    return [
        {
            "grupo_comercial_id": "F213",
            "nome_grupo_comercial": "FIPAL CONSTRUTORA",
            "data_primeira_compra": "2026-09-01",
            "pedidos": "01101/058349",
            "vendedor": "Vendedor A",
            "regiao": "SUL 01",
            "segmento": "Construção",
            "situacao_atribuicao": "Integral",
            "xp": 10,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_primeira_compra": "2026-09-10",
            "pedidos": "01101/058691 · 01101/058697",
            "vendedor": "Vendedor B",
            "regiao": "NORTE 01",
            "segmento": "Construção",
            "situacao_atribuicao": "Divisão 50/50",
            "xp": 5,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_primeira_compra": "2026-09-10",
            "pedidos": "01101/058691 · 01101/058697",
            "vendedor": "Vendedor C",
            "regiao": "NORTE 02",
            "segmento": "Construção",
            "situacao_atribuicao": "Divisão 50/50",
            "xp": 5,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO PENDENTE",
            "data_primeira_compra": "2026-09-12",
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


def test_repository_loads_new_customers_with_month_parameter():
    client = FakeClient(sample_rows())
    rows = NewCustomersRepository(client).load(MONTH)

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": "2026-09-01"})]
    assert rows[0]["grupo_comercial_id"] == "F213"
    assert rows[0]["vendedor"] == "Vendedor A"
    assert rows[1]["xp"] == 5


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        NewCustomersRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_repository_loads_whole_campaign_without_competence_filter():
    client = FakeClient(sample_rows())
    NewCustomersRepository(client).load()
    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": None})]


def test_sql_applies_confirmed_new_customer_rules():
    sql = Path("sql/clientes_novos.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "set statement_timeout = '60s'" in sql
    assert "#variable_conflict use_column" in sql
    assert "grant execute on function public.campanha_polar_carregar_clientes_novos(date)" in sql
    assert "date '2022-01-01'" in sql
    assert "vw_clientes_inadimplentes" in sql
    assert "fct_faturamento_item" in sql
    assert "fct_nota_devolucao" in sql
    assert "count(distinct (a.filial_id, a.pedido_id))" in sql
    assert "then 10.0 / n.quantidade_vendedores" in sql
    assert "detalhes as (" in sql
    assert "inner join detalhes as d" in sql
    assert "m.meta > 0" in sql


def page_runner():
    import streamlit as st
    from app import render_new_customers

    render_new_customers(st.session_state["repo"])


def test_page_renders_only_region_filter_summary_and_detailed_table():
    repository = SimpleNamespace(load=lambda: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert len(app.metric) == 0
    assert len(app.selectbox) == 1
    assert app.selectbox[0].label == "Região"
    assert len(app.dataframe) == 1
    summary_html = next(
        block.value for block in app.markdown if "polar-summary-table" in block.value
    )
    assert summary_html.count("<tr>") == 4
    assert "GRUPO PENDENTE</div><div class='polar-summary-item'>PLANO INCORPORAÇÕES" in summary_html
    assert list(app.dataframe[0].value.columns) == [
        "Data",
        "Grupo comercial",
        "Pedido de venda",
        "Vendedores",
        "Região",
        "Segmento",
        "Atribuição",
        "XP",
    ]
    assert len(app.dataframe[0].value) == 4
    triangulation = app.dataframe[0].value[
        app.dataframe[0].value["Grupo comercial"] == "PLANO INCORPORAÇÕES"
    ]
    assert list(triangulation["Vendedores"]) == ["Vendedor B", "Vendedor C"]
    assert list(triangulation["Região"]) == ["NORTE 01", "NORTE 02"]
    assert list(triangulation["XP"]) == [5.0, 5.0]


def test_region_summary_counts_clients_and_allocates_event_xp():
    import pandas as pd

    from app import build_new_customers_region_summary

    summary = build_new_customers_region_summary(pd.DataFrame(sample_rows())).set_index("Região")

    assert summary.loc["SUL 01", "Quantidade de clientes novos"] == 1
    assert summary.loc["SUL 01", "Total XP"] == pytest.approx(10)
    assert summary.loc["NORTE 01", "Quantidade de clientes novos"] == 2
    assert summary.loc["NORTE 01", "Lista dos clientes novos"].splitlines() == [
        "GRUPO PENDENTE", "PLANO INCORPORAÇÕES",
    ]
    assert summary.loc["NORTE 01", "Total XP"] == pytest.approx(5)
    assert summary.loc["NORTE 02", "Quantidade de clientes novos"] == 1
    assert summary.loc["NORTE 02", "Total XP"] == pytest.approx(5)


def test_region_summary_keeps_full_xp_for_two_sellers_in_same_region():
    import pandas as pd

    from app import build_new_customers_region_summary

    rows = [
        {
            "grupo_comercial_id": "F300",
            "nome_grupo_comercial": "CLIENTE TRIANGULADO",
            "regiao": "SUL 01",
            "xp": 5,
        },
        {
            "grupo_comercial_id": "F300",
            "nome_grupo_comercial": "CLIENTE TRIANGULADO",
            "regiao": "SUL 01",
            "xp": 5,
        },
    ]
    summary = build_new_customers_region_summary(pd.DataFrame(rows)).iloc[0]

    assert summary["Quantidade de clientes novos"] == 1
    assert summary["Total XP"] == pytest.approx(10)
