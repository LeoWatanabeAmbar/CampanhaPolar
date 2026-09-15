from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest
from postgrest.exceptions import APIError

from polar.adiantamento import DataAccessError
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
            "vendedor": "Vendedor A",
            "regiao": "SUL 01",
            "segmento": "Construção",
            "valor_linha_elegivel": 3500,
            "valor_minimo": 3000,
            "situacao_evento": "Confirmado: integral",
            "xp": 10,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_expansao": "2026-09-10",
            "grupo_mix": "Suporte de Bancada",
            "produtos": "002917",
            "pedidos": "01101/058691 · 01101/058697",
            "vendedor": "Vendedor B",
            "regiao": "NORTE 01",
            "segmento": "Construção",
            "valor_linha_elegivel": 10000,
            "valor_minimo": 9000,
            "situacao_evento": "Confirmado: divisão 50/50",
            "xp": 5,
        },
        {
            "grupo_comercial_id": "F224",
            "nome_grupo_comercial": "PLANO INCORPORAÇÕES",
            "data_expansao": "2026-09-10",
            "grupo_mix": "Suporte de Bancada",
            "produtos": "002917",
            "pedidos": "01101/058691 · 01101/058697",
            "vendedor": "Vendedor C",
            "regiao": "NORTE 02",
            "segmento": "Construção",
            "valor_linha_elegivel": 10000,
            "valor_minimo": 9000,
            "situacao_evento": "Confirmado: divisão 50/50",
            "xp": 5,
        },
        {
            "grupo_comercial_id": "F999",
            "nome_grupo_comercial": "GRUPO COM DEVOLUÇÃO",
            "data_expansao": "2026-09-12",
            "grupo_mix": "CPP 009",
            "produtos": "000010",
            "pedidos": "01101/058999",
            "vendedor": "Vendedor D",
            "regiao": "CANAIS 01",
            "segmento": "Canais",
            "valor_linha_elegivel": 2500,
            "valor_minimo": 2200,
            "situacao_evento": "Pendente: devolução na nota do pedido",
            "xp": 0,
        },
        {
            "grupo_comercial_id": "C02",
            "nome_grupo_comercial": "MRV",
            "data_expansao": "2026-09-13",
            "grupo_mix": "Hydrofix",
            "produtos": "002920",
            "pedidos": "01101/059000",
            "vendedor": "Vendedor E",
            "regiao": "NORTE 01",
            "segmento": "Construção",
            "valor_linha_elegivel": 4000,
            "valor_minimo": 3000,
            "situacao_evento": "Sem XP: cliente KA",
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


class RejectedClient:
    def rpc(self, function, parameters):
        raise APIError({"code": "PGRST202", "message": "Function not found in schema cache"})


def test_repository_loads_whole_campaign():
    client = FakeClient(sample_rows())
    rows = ProductMixRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {"p_competencia": None})]
    assert rows[0]["valor_minimo"] == pytest.approx(3000)
    assert rows[1]["xp"] == 5


def test_repository_rejects_invalid_month_before_rpc():
    client = FakeClient([])
    with pytest.raises(ValueError):
        ProductMixRepository(client).load(date(2026, 8, 1))
    assert client.calls == []


def test_repository_reports_data_api_error_code_and_message():
    with pytest.raises(DataAccessError) as captured:
        ProductMixRepository(RejectedClient()).load()

    assert "PGRST202" in str(captured.value)
    assert "Function not found in schema cache" in str(captured.value)


def test_sql_applies_mix_rules():
    sql = Path("sql/mix_produtos.sql").read_text(encoding="utf-8").lower()
    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "grant execute on function public.campanha_polar_carregar_mix_produtos(date)" in sql
    assert "#variable_conflict use_column" in sql
    assert "notify pgrst, 'reload schema'" in sql
    assert "('002920'::text, 'hydrofix'::text)" in sql
    assert "('003027', 'suporte de bancada')" in sql
    assert "grupos_ka(grupo_comercial_id)" in sql
    assert "then 3000" in sql
    assert "then 9000" in sql
    assert "then 2200" in sql
    assert "notas_pedido as (" in sql
    assert "pedidos_com_devolucao as (" in sql
    assert "n.nota_fiscal_id = trim(d.nota_fiscal_original_id)" in sql
    assert "dv.pedido_id = v.pedido_id" in sql
    assert "pendente: devolução na nota do pedido" in sql
    assert "grupos_com_devolucao_sem_produto" not in sql
    assert "then 10.0 / p.quantidade_vendedores" in sql
    assert "detalhes as (" in sql
    assert "inner join detalhes as d" in sql


def page_runner():
    import streamlit as st
    from app import render_product_mix

    render_product_mix(st.session_state["repo"])


def test_page_renders_mix_summary_region_filter_and_details():
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
        "Região", "Quantidade de expansões", "Lista das expansões", "Total XP",
    ]
    detail = app.dataframe[1].value
    assert list(detail.columns) == [
        "Data", "Grupo comercial", "Família", "Produtos", "Pedido de venda",
        "Vendedores", "Região", "Segmento", "Valor da linha", "Mínimo", "Resultado", "XP",
    ]
    triangulation = detail[detail["Grupo comercial"] == "PLANO INCORPORAÇÕES"]
    assert list(triangulation["Vendedores"]) == ["Vendedor B", "Vendedor C"]
    assert list(triangulation["Região"]) == ["NORTE 01", "NORTE 02"]
    assert list(triangulation["XP"]) == [5.0, 5.0]


def test_page_handles_previous_data_contract_without_keyerror():
    legacy_row = {
        "grupo_comercial_id": "F213",
        "nome_grupo_comercial": "FIPAL CONSTRUTORA",
        "data_expansao": "2026-09-01",
        "grupo_mix": "Hydrofix",
        "regioes": "SUL 01",
        "xp_por_vendedor": 10,
    }
    app = AppTest.from_function(page_runner)
    app.session_state["repo"] = SimpleNamespace(load=lambda: [legacy_row])
    app.run(timeout=15)

    assert not app.exception
    assert len(app.warning) == 1
    assert "formato anterior" in app.warning[0].value
    assert "mix_produtos.sql" in app.warning[0].value


def test_mix_region_summary_counts_expansion_once_and_ignores_zero_xp():
    import pandas as pd

    from app import build_product_mix_region_summary

    summary = build_product_mix_region_summary(pd.DataFrame(sample_rows())).set_index("Região")

    assert summary.loc["SUL 01", "Quantidade de expansões"] == 1
    assert summary.loc["SUL 01", "Total XP"] == pytest.approx(10)
    assert summary.loc["NORTE 01", "Quantidade de expansões"] == 1
    assert summary.loc["NORTE 01", "Total XP"] == pytest.approx(5)
    assert summary.loc["NORTE 02", "Quantidade de expansões"] == 1
    assert summary.loc["NORTE 02", "Total XP"] == pytest.approx(5)
    assert "CANAIS 01" not in summary.index
