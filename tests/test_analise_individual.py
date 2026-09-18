"""Testes da consolidação e navegação da página Análise individual."""

from datetime import date
from decimal import Decimal
import json
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.vendas import SEPTEMBER


def advancement_rows():
    return {
        SEPTEMBER: [
            {
                "regiao": "REG A",
                "semana_1_32": True,
                "semana_2_56": True,
                "semana_3_80": False,
                "observacao": "Duas fases confirmadas",
            },
            {
                "regiao": "REG B",
                "semana_1_32": False,
                "semana_2_56": False,
                "semana_3_80": False,
                "observacao": "",
            },
        ],
    }


def new_rows():
    return [
        {
            "grupo_comercial_id": "N1",
            "nome_grupo_comercial": "CLIENTE NOVO A",
            "data_primeira_compra": "2026-09-01",
            "pedidos": "01101/058001",
            "vendedor": "Vendedor A",
            "regiao": "REG A",
            "segmento": "Canais",
            "situacao_atribuicao": "Integral",
            "xp": 10,
        },
        {
            "grupo_comercial_id": "N2",
            "nome_grupo_comercial": "CLIENTE NOVO B",
            "data_primeira_compra": "2026-09-02",
            "pedidos": "01101/058002",
            "vendedor": "Vendedor B",
            "regiao": "REG B",
            "segmento": "Canais",
            "situacao_atribuicao": "Integral",
            "xp": 10,
        },
    ]


def reactivated_rows():
    return [{
        "grupo_comercial_id": "R1",
        "nome_grupo_comercial": "CLIENTE REATIVADO A",
        "data_reativacao": "2026-09-03",
        "data_ultima_compra": "2025-10-01",
        "prazo_meses": 6,
        "pedidos": "01101/058003",
        "vendedor": "Vendedor A",
        "regiao": "REG A",
        "segmento": "Canais",
        "situacao_atribuicao": "Integral",
        "xp": 8,
    }]


def mix_rows():
    common = {
        "grupo_comercial_id": "M1",
        "nome_grupo_comercial": "CLIENTE MIX A",
        "data_primeira_compra_familia": "2026-09-04",
        "grupo_mix": "Hydrofix",
        "produtos": "002920",
        "vendedor": "Vendedor A",
        "regiao": "REG A",
        "segmento": "Canais",
        "valor_minimo": 3000,
    }
    return [
        {
            **common,
            "data_expansao": "2026-09-04",
            "pedidos": "01101/058004",
            "valor_linha_elegivel": 3500,
            "situacao_evento": "Elegível: integral",
            "xp": 10,
        },
        {
            **common,
            "data_expansao": "2026-09-12",
            "pedidos": "01101/058012",
            "valor_linha_elegivel": 1000,
            "situacao_evento": "Sem XP: família comprada anteriormente",
            "xp": 0,
        },
    ]


def sales_rows():
    return [{
        "data_referencia": "2026-09-16",
        "regiao": "REG A",
        "time": "CANAIS",
        "meta": Decimal("210000"),
        "realizado": Decimal("121000"),
        "vendedores": "Vendedor A",
    }]


def page_runner():
    from datetime import date

    import streamlit as st
    from app import render_individual_analysis

    render_individual_analysis(
        st.session_state["advancement_repo"],
        st.session_state["new_repo"],
        st.session_state["reactivated_repo"],
        st.session_state["mix_repo"],
        st.session_state["sales_repo"],
        date(2026, 9, 16),
    )


def test_individual_analysis_shows_total_breakdown_and_region_details():
    app = AppTest.from_function(page_runner)
    app.session_state["advancement_repo"] = SimpleNamespace(
        load_campaign=advancement_rows
    )
    app.session_state["new_repo"] = SimpleNamespace(load=new_rows)
    app.session_state["reactivated_repo"] = SimpleNamespace(load=reactivated_rows)
    app.session_state["mix_repo"] = SimpleNamespace(load=mix_rows)
    app.session_state["sales_repo"] = SimpleNamespace(
        load_through=lambda reference: {SEPTEMBER: sales_rows()}
    )
    app.run(timeout=15)

    assert not app.exception
    assert len(app.selectbox) == 1
    assert app.selectbox[0].label == "Região"
    assert app.selectbox[0].value == "REG A"
    assert [metric.label for metric in app.metric] == [
        "XP total",
        "Classificação",
        "Clientes novos",
        "Clientes reativados",
        "Expansão de mix",
        "Atingimento de meta",
        "Adiantamento",
    ]
    assert [metric.value for metric in app.metric[:2]] == ["598 XP", "Prata"]
    assert [metric.value for metric in app.metric[2:]] == [
        "10 XP", "8 XP", "10 XP", "550 XP", "20 XP",
    ]
    chart_spec = json.loads(app.get("vega_lite_chart")[0].proto.spec)
    assert chart_spec["encoding"]["x"]["field"] == "XP"
    assert chart_spec["encoding"]["y"]["field"] == "Indicador"
    assert [tab.label for tab in app.tabs] == [
        "Clientes novos",
        "Clientes reativados",
        "Expansão de mix",
        "Venda x meta",
        "Adiantamento",
    ]
    assert len(app.dataframe) == 5
    assert app.dataframe[0].value["Grupo comercial"].tolist() == ["CLIENTE NOVO A"]
    assert app.dataframe[1].value["Grupo comercial"].tolist() == ["CLIENTE REATIVADO A"]
    assert app.dataframe[2].value["Resultado"].tolist() == [
        "Elegível: integral", "Sem XP: família comprada anteriormente",
    ]
    assert app.dataframe[3].value.iloc[0]["XP da região"] == pytest.approx(550)
    assert app.dataframe[4].value.iloc[0]["XP"] == pytest.approx(20)


def test_individual_analysis_updates_all_totals_when_region_changes():
    app = AppTest.from_function(page_runner)
    app.session_state["advancement_repo"] = SimpleNamespace(
        load_campaign=advancement_rows
    )
    app.session_state["new_repo"] = SimpleNamespace(load=new_rows)
    app.session_state["reactivated_repo"] = SimpleNamespace(load=reactivated_rows)
    app.session_state["mix_repo"] = SimpleNamespace(load=mix_rows)
    app.session_state["sales_repo"] = SimpleNamespace(
        load_through=lambda reference: {SEPTEMBER: sales_rows()}
    )
    app.run(timeout=15)
    app.selectbox[0].set_value("REG B").run(timeout=15)

    assert not app.exception
    assert [metric.value for metric in app.metric[:2]] == [
        "10 XP", "Sem classificação",
    ]
    assert [metric.value for metric in app.metric[2:]] == [
        "10 XP", "0 XP", "0 XP", "0 XP", "0 XP",
    ]
    assert len(app.dataframe) == 2
    assert app.dataframe[0].value["Grupo comercial"].tolist() == ["CLIENTE NOVO B"]
    assert app.dataframe[1].value.iloc[0]["XP"] == pytest.approx(0)
