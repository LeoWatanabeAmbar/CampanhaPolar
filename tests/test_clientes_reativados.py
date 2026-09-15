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
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor A",
            "regioes": "CANAIS 01",
            "segmento": "Canais",
            "valor_liquido_elegivel": 7807.25,
            "quantidade_vendedores": 1,
            "situacao_atribuicao": "Integral",
            "xp_evento": 8,
            "xp_por_vendedor": 8,
        },
        {
            "grupo_comercial_id": "CB2",
            "nome_grupo_comercial": "URBEN PARTICIPAÇÕES",
            "data_reativacao": "2026-09-04",
            "data_ultima_compra": "2025-05-08",
            "prazo_meses": 12,
            "pedidos": "01101/058578",
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor B · Vendedor C",
            "regioes": "NORTE 01 · NORTE 02",
            "segmento": "Construção",
            "valor_liquido_elegivel": 3722.80,
            "quantidade_vendedores": 2,
            "situacao_atribuicao": "Divisão 50/50",
            "xp_evento": 8,
            "xp_por_vendedor": 4,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO PENDENTE",
            "data_reativacao": "2026-09-12",
            "data_ultima_compra": "2025-01-01",
            "prazo_meses": 12,
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


def test_repository_loads_whole_campaign():
    client = FakeClient(sample_rows())
    rows = ReactivatedCustomersRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": None})]
    assert rows[0]["prazo_meses"] == 6
    assert rows[1]["xp_por_vendedor"] == 4


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        ReactivatedCustomersRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_sql_applies_reactivation_rules():
    sql = Path("sql/clientes_reativados.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "grant execute on function public.campanha_polar_carregar_clientes_reativados(date)" in sql
    assert "interval '6 months'" in sql
    assert "interval '12 months'" in sql
    assert "lag(e.data_emissao)" in sql
    assert "then 8.0 / r.quantidade_vendedores" in sql
    assert "vw_clientes_inadimplentes" in sql
    assert "fct_nota_devolucao" in sql


def page_runner():
    import streamlit as st
    from app import render_reactivated_customers

    render_reactivated_customers(st.session_state["repo"])


def test_page_renders_reactivated_metrics_warning_and_table():
    repository = SimpleNamespace(load=lambda: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Clientes reativados",
        "Pedidos no retorno",
        "Valor líquido elegível",
        "XP bruto confirmado",
    ]
    assert app.metric[0].value == "3"
    assert app.metric[3].value == "16 XP"
    assert len(app.warning) == 1
    assert len(app.dataframe) == 1
