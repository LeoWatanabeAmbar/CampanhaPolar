from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.mix_produtos import LOAD_FUNCTION, ProductMixRepository


def sample_rows():
    return [
        {
            "grupo_comercial_id": "F213",
            "nome_grupo_comercial": "FIPAL CONSTRUTORA",
            "data_expansao": "2026-09-01",
            "grupo_mix": "Hydrofix",
            "produtos": "002920 · 002921",
            "pedidos": "01101/058349",
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor A",
            "regioes": "SUL 01",
            "segmento": "Construção",
            "valor_linha_elegivel": 3500,
            "valor_minimo": 3000,
            "quantidade_vendedores": 1,
            "situacao_evento": "Confirmado: integral",
            "xp_evento": 10,
            "xp_por_vendedor": 10,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_expansao": "2026-09-10",
            "grupo_mix": "Suporte de Bancada",
            "produtos": "002917",
            "pedidos": "01101/058691 · 01101/058697",
            "quantidade_pedidos": 2,
            "vendedores": "Vendedor B · Vendedor C",
            "regioes": "NORTE 01 · NORTE 02",
            "segmento": "Construção",
            "valor_linha_elegivel": 10000,
            "valor_minimo": 9000,
            "quantidade_vendedores": 2,
            "situacao_evento": "Confirmado: divisão 50/50",
            "xp_evento": 10,
            "xp_por_vendedor": 5,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO COM DEVOLUÇÃO",
            "data_expansao": "2026-09-12",
            "grupo_mix": "CPP 009",
            "produtos": "000010",
            "pedidos": "01101/058999",
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor D",
            "regioes": "CANAIS 01",
            "segmento": "Canais",
            "valor_linha_elegivel": 2500,
            "valor_minimo": 2200,
            "quantidade_vendedores": 1,
            "situacao_evento": "Pendente: devolução sem produto",
            "xp_evento": 0,
            "xp_por_vendedor": 0,
        },
        {
            "grupo_comercial_id": "C02",
            "nome_grupo_comercial": "MRV",
            "data_expansao": "2026-09-13",
            "grupo_mix": "Hydrofix",
            "produtos": "002920",
            "pedidos": "01101/059000",
            "quantidade_pedidos": 1,
            "vendedores": "Vendedor E",
            "regioes": "NORTE 01",
            "segmento": "Construção",
            "valor_linha_elegivel": 4000,
            "valor_minimo": 3000,
            "quantidade_vendedores": 1,
            "situacao_evento": "Sem XP: cliente KA",
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
    rows = ProductMixRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": None})]
    assert rows[0]["valor_minimo"] == pytest.approx(3000)
    assert rows[1]["xp_por_vendedor"] == 5


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        ProductMixRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_sql_applies_mix_rules():
    sql = Path("sql/mix_produtos.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "grant execute on function public.campanha_polar_carregar_mix_produtos(date)" in sql
    assert "('002920'::text, 'hydrofix'::text)" in sql
    assert "('003027', 'suporte de bancada')" in sql
    assert "grupos_ka(grupo_comercial_id)" in sql
    assert "then 3000" in sql
    assert "then 9000" in sql
    assert "then 2200" in sql
    assert "pendente: devolução sem produto" in sql
    assert "then 10.0 / p.quantidade_vendedores" in sql


def page_runner():
    import streamlit as st
    from app import render_product_mix

    render_product_mix(st.session_state["repo"])


def test_page_renders_mix_metrics_warning_and_table():
    repository = SimpleNamespace(load=lambda: sample_rows())
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Linhas avaliadas",
        "Expansões confirmadas",
        "Valor das linhas",
        "XP confirmado",
    ]
    assert app.metric[0].value == "4"
    assert app.metric[1].value == "2"
    assert app.metric[3].value == "20 XP"
    assert len(app.warning) == 1
    assert len(app.dataframe) == 1
