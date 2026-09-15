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
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor A",
            "regioes": "SUL 01",
            "segmento": "Construção",
            "valor_liquido_elegivel": 11941.47,
            "quantidade_vendedores": 1,
            "situacao_atribuicao": "Integral",
            "xp_evento": 10,
            "xp_por_vendedor": 10,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_primeira_compra": "2026-09-10",
            "pedidos": "01101/058691 · 01101/058697",
            "quantidade_pedidos": 2,
            "vendedores": "Vendedor B · Vendedor C",
            "regioes": "NORTE 01 · NORTE 02",
            "segmento": "Construção",
            "valor_liquido_elegivel": 54247.08,
            "quantidade_vendedores": 2,
            "situacao_atribuicao": "Divisão 50/50",
            "xp_evento": 10,
            "xp_por_vendedor": 5,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO PENDENTE",
            "data_primeira_compra": "2026-09-12",
            "pedidos": "01101/058999",
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor D",
            "regioes": "NORTE 01",
            "segmento": "Construção",
            "valor_liquido_elegivel": 1000,
            "quantidade_vendedores": 1,
            "situacao_atribuicao": "Pendente: região sem meta",
            "xp_evento": 0,
            "xp_por_vendedor": 0,
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
    assert rows[0]["valor_liquido_elegivel"] == pytest.approx(11941.47)
    assert rows[1]["xp_por_vendedor"] == 5


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        NewCustomersRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_sql_applies_confirmed_new_customer_rules():
    sql = Path("sql/clientes_novos.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "grant execute on function public.campanha_polar_carregar_clientes_novos(date)" in sql
    assert "date '2022-01-01'" in sql
    assert "vw_clientes_inadimplentes" in sql
    assert "fct_faturamento_item" in sql
    assert "fct_nota_devolucao" in sql
    assert "count(distinct (a.filial_id, a.pedido_id))" in sql
    assert "then 10.0 / n.quantidade_vendedores" in sql
    assert "m.meta > 0" in sql


def page_runner():
    import streamlit as st
    from datetime import date
    from app import render_new_customers

    render_new_customers(st.session_state["repo"], date(2026, 9, 1))


def test_page_renders_metrics_pending_warning_and_table():
    repository = SimpleNamespace(load=lambda month: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Clientes novos",
        "Pedidos no primeiro evento",
        "Valor líquido elegível",
        "XP bruto confirmado",
    ]
    assert app.metric[0].value == "3"
    assert app.metric[3].value == "20 XP"
    assert len(app.warning) == 1
    assert len(app.dataframe) == 1
