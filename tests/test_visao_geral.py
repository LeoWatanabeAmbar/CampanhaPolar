"""Testes da consolidação regional, classificação e cartão de budget."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from polar.vendas import SEPTEMBER


def advancement_rows():
    return {
        SEPTEMBER: [
            {
                "regiao": "REG 01", "semana_1_32": True,
                "semana_2_56": True, "semana_3_80": False,
            },
            {
                "regiao": "REG 02", "semana_1_32": False,
                "semana_2_56": False, "semana_3_80": False,
            },
        ],
        date(2026, 10, 1): [
            {
                "regiao": "REG 01", "semana_1_32": True,
                "semana_2_56": False, "semana_3_80": False,
            },
        ],
    }


def new_rows():
    return [
        {"regiao": "REG 01", "vendedor": "A", "xp": 70},
        {"regiao": "REG 01", "vendedor": "A", "xp": 40},
        {"regiao": "REG 01", "vendedor": "B", "xp": 5},
        {"regiao": "REG 02", "vendedor": "C", "xp": 10},
    ]


def reactivated_rows():
    return [
        {"regiao": "REG 01", "vendedor": "A", "xp": 60},
        {"regiao": "REG 01", "vendedor": "A", "xp": 30},
        {"regiao": "REG 02", "vendedor": "C", "xp": 8},
    ]


def mix_rows():
    return [
        {"regiao": "REG 01", "vendedor": "A", "xp": 10},
        {"regiao": "REG 01", "vendedor": "B", "xp": 5},
        {"regiao": "REG 02", "vendedor": "C", "xp": 10},
    ]


def sales_results():
    return [
        {"regiao": "REG 01", "xp": 550},
        {"regiao": "REG 02", "xp": 450},
    ]


def test_overview_consolidates_xp_by_region_and_applies_seller_caps():
    from app import build_xp_overview_frame

    frame = build_xp_overview_frame(
        advancement_rows(), new_rows(), reactivated_rows(), mix_rows(), sales_results()
    ).set_index("Região")

    assert frame.loc["REG 01", "XP por cliente novo"] == pytest.approx(105)
    assert frame.loc["REG 01", "XP por cliente reativado"] == pytest.approx(80)
    assert frame.loc["REG 01", "XP por expansão de mix"] == pytest.approx(15)
    assert frame.loc["REG 01", "XP por atingimento de meta"] == pytest.approx(550)
    assert frame.loc["REG 01", "XP por adiantamento"] == pytest.approx(30)
    assert frame.loc["REG 01", "XP total"] == pytest.approx(780)
    assert frame.loc["REG 01", "Classificação"] == "Prata"
    assert frame.loc["REG 02", "XP total"] == pytest.approx(478)
    assert frame.loc["REG 02", "Classificação"] == "Bronze"


@pytest.mark.parametrize(("xp", "expected"), [
    (369, "Sem classificação"),
    (370, "Bronze"),
    (500, "Bronze"),
    (501, "Prata"),
    (800, "Prata"),
    (801, "Ouro"),
    (1_039, "Ouro"),
    (1_040, "Diamante"),
    (1_200, "Diamante"),
    (1_201, "Polar"),
])
def test_campaign_classification_uses_documented_boundaries(xp, expected):
    from app import campaign_classification

    assert campaign_classification(xp) == expected


def test_overview_orders_regions_by_total_xp_descending():
    from app import build_xp_overview_frame

    frame = build_xp_overview_frame(
        {},
        [
            {"regiao": "REG A", "vendedor": "A", "xp": 10},
            {"regiao": "REG Z", "vendedor": "Z", "xp": 20},
        ],
        [],
        [],
        [],
    )

    assert frame["Região"].tolist() == ["REG Z", "REG A"]


def overview_runner():
    from datetime import date

    import streamlit as st
    from app import render_overview

    render_overview(
        st.session_state["advancement_repo"],
        st.session_state["new_repo"],
        st.session_state["reactivated_repo"],
        st.session_state["mix_repo"],
        st.session_state["sales_repo"],
        st.session_state["budget_repo"],
        date(2026, 9, 16),
    )


def test_overview_renders_only_budget_graph_and_requested_xp_table():
    sales_rows = [
        {
            "data_referencia": "2026-09-16", "regiao": "REG 01", "time": "TIME SUL",
            "meta": Decimal("210000"), "realizado": Decimal("121000"),
            "vendedores": "A · B",
        },
        {
            "data_referencia": "2026-09-16", "regiao": "REG 02", "time": "CANAIS",
            "meta": Decimal("210000"), "realizado": Decimal("99000"),
            "vendedores": "C",
        },
    ]
    app = AppTest.from_function(overview_runner)
    app.session_state["advancement_repo"] = SimpleNamespace(
        load_campaign=lambda: advancement_rows()
    )
    app.session_state["new_repo"] = SimpleNamespace(load=new_rows)
    app.session_state["reactivated_repo"] = SimpleNamespace(load=reactivated_rows)
    app.session_state["mix_repo"] = SimpleNamespace(load=mix_rows)
    app.session_state["sales_repo"] = SimpleNamespace(
        load_through=lambda reference: {SEPTEMBER: sales_rows}
    )
    app.session_state["budget_repo"] = SimpleNamespace(load=lambda: {
        "data_referencia": "2026-09-16",
        "realizado": Decimal("59500000"),
        "budget": Decimal("119000000"),
        "atingimento_pct": Decimal("50"),
    })
    app.run(timeout=15)

    assert not app.exception
    assert len(app.metric) == 0
    assert [heading.value for heading in app.subheader] == [
        "Atingimento do budget anual de vendas", "XP por região",
    ]
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert list(table.columns) == [
        "Região",
        "Classificação",
        "XP por cliente novo",
        "XP por cliente reativado",
        "XP por expansão de mix",
        "XP por atingimento de meta",
        "XP por adiantamento",
        "XP total",
    ]
    assert table["Região"].tolist() == ["REG 01", "REG 02"]
    assert table.set_index("Região").loc["REG 01", "XP total"] == pytest.approx(780)


def test_budget_card_keeps_currency_readable_and_separates_values():
    from app import build_budget_card_html

    html = build_budget_card_html({
        "data_referencia": "2026-09-16",
        "realizado": Decimal("77513456"),
        "budget": Decimal("119000000"),
        "atingimento_pct": Decimal("65.137358"),
    })

    assert "65,1%" in html
    assert "R$ 77.513.456" in html
    assert "R$ 119.000.000" in html
    assert "16/09/2026" in html
    assert "width: 65.1374%" in html
