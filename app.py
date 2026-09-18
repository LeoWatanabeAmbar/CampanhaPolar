"""Interface web da campanha XP Polar.

Este módulo é deliberadamente responsável apenas pela composição da interface e
pelas consolidações que precisam acontecer depois das consultas. Regras pesadas
de elegibilidade vivem nas funções SQL; autenticação e contratos da Data API
ficam nos módulos de ``polar``. Essa separação evita reproduzir regras de negócio
em cada página do Streamlit.
"""
from __future__ import annotations

from datetime import date, datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from polar.autenticacao import AuthenticationServiceError, SupabaseAuthenticator
from polar.atualizacao import DataRefreshRepository
from polar.budget import BudgetRepository
from polar.adiantamento import (
    EDITOR_EMAILS,
    FIELDS,
    ConcurrentChange,
    DataAccessError,
    Identity,
    PermissionDenied,
    Repository,
)
from polar.clientes_novos import NewCustomersRepository
from polar.clientes_reativados import ReactivatedCustomersRepository
from polar.mix_produtos import ProductMixRepository
from polar.vendas import SalesRepository, calculate_cumulative_region_results

# A campanha é fixa em 2026. Estes rótulos são somente de apresentação; a
# validação das competências fica centralizada em polar.adiantamento.
MONTHS = {9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
MONTH_ABBREVIATIONS = {9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
ADVANCE_SUFFIXES = {
    "semana_1_32": "1ª semana - 32%",
    "semana_2_56": "2ª semana - 56%",
    "semana_3_80": "3ª semana - 80%",
}
LABELS = {
    "regiao": "Região",
    "semana_1_32": "1ª semana · 32%",
    "semana_2_56": "2ª semana · 56%",
    "semana_3_80": "3ª semana · 80%",
    "observacao": "Observações",
}
# Tokens visuais compartilhados pelo CSS injetado e pelos gráficos nativos.
POLAR_BLUE = "#0072D6"
POLAR_BLUE_DARK = "#005DAD"
POLAR_BLUE_SOFT = "#E8F3FC"
POLAR_INK = "#17233A"
POLAR_BORDER = "#DCE8F4"
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo_polar_horizontal.png"
PAGE_ICON_PATH = Path(__file__).resolve().parent / "assets" / "icone_polar.png"


def apply_polar_style():
    """Replica a identidade visual usada no Gestão Comercial."""
    # O Streamlit não oferece todos esses ajustes via config.toml. O CSS fica
    # concentrado aqui para não espalhar estilos pelas funções de página.
    st.markdown(
        f"""
        <style>
        :root {{
            --polar-blue: {POLAR_BLUE};
            --polar-blue-dark: {POLAR_BLUE_DARK};
            --polar-blue-soft: {POLAR_BLUE_SOFT};
            --polar-ink: {POLAR_INK};
            --polar-border: {POLAR_BORDER};
        }}

        .stApp {{ background: #FFFFFF; color: var(--polar-ink); }}
        .block-container {{ max-width: 1480px; padding-top: 2rem; padding-bottom: 3rem; }}
        h1, h2, h3 {{ color: var(--polar-ink); }}
        h1 {{ font-weight: 750; letter-spacing: -0.025em; }}
        [data-testid="stCaptionContainer"] {{ color: #5C6F86; }}
        [data-testid="stSidebar"] {{
            background: #F4F8FC;
            border-right: 1px solid var(--polar-border);
        }}

        .polar-kicker {{
            color: var(--polar-blue);
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.09em;
            margin-bottom: 0.4rem;
            text-transform: uppercase;
        }}
        .polar-page-title {{
            color: var(--polar-ink);
            font-size: 2.25rem;
            font-weight: 760;
            letter-spacing: -0.035em;
            line-height: 1.1;
            margin: 0;
        }}
        .polar-page-subtitle {{
            color: #5C6F86;
            font-size: 1rem;
            margin: 0.55rem 0 1.65rem;
        }}

        div[data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid var(--polar-border);
            border-left: 4px solid var(--polar-blue);
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(23, 35, 58, 0.04);
            min-height: 112px;
            padding: 0.8rem 0.9rem;
        }}
        div[data-testid="stMetricLabel"] p {{ color: #5C6F86; }}
        div[data-testid="stMetricValue"] {{ color: var(--polar-ink); }}

        .polar-budget-card {{
            background: linear-gradient(135deg, #F7FBFF 0%, #E8F3FC 100%);
            border: 1px solid var(--polar-border);
            border-left: 5px solid var(--polar-blue);
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(23, 35, 58, 0.07);
            margin-bottom: 1.75rem;
            padding: 1.25rem 1.4rem;
        }}
        .polar-budget-grid {{
            align-items: end;
            display: grid;
            gap: 1rem 2rem;
            grid-template-columns: minmax(150px, 0.7fr) repeat(2, minmax(190px, 1fr));
        }}
        .polar-budget-label {{
            color: #5C6F86;
            display: block;
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.07em;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
        }}
        .polar-budget-percentage {{
            color: var(--polar-blue);
            font-size: 2.2rem;
            font-weight: 780;
            letter-spacing: -0.04em;
            line-height: 1;
        }}
        .polar-budget-value {{
            color: var(--polar-ink);
            font-size: 1.25rem;
            font-weight: 720;
            white-space: nowrap;
        }}
        .polar-budget-track {{
            background: #D5E5F4;
            border-radius: 999px;
            height: 12px;
            margin-top: 1.15rem;
            overflow: hidden;
        }}
        .polar-budget-fill {{
            background: linear-gradient(90deg, var(--polar-blue), #35A0F2);
            border-radius: 999px;
            height: 100%;
        }}
        .polar-budget-reference {{
            color: #5C6F86;
            font-size: 0.85rem;
            margin-top: 0.65rem;
        }}
        @media (max-width: 760px) {{
            .polar-budget-grid {{ grid-template-columns: 1fr; }}
        }}

        .stButton > button, .stDownloadButton > button {{
            border-color: var(--polar-blue);
            border-radius: 6px;
            color: var(--polar-blue);
            font-weight: 600;
        }}
        .stButton > button[kind="primary"],
        .stDownloadButton > button[kind="primary"] {{
            background: var(--polar-blue);
            border-color: var(--polar-blue);
            color: #FFFFFF;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            border-color: var(--polar-blue-dark);
            color: var(--polar-blue-dark);
        }}
        .stButton > button[kind="primary"]:hover {{
            background: var(--polar-blue-dark);
            color: #FFFFFF;
        }}

        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
            border: 1px solid var(--polar-border);
            border-radius: 8px;
            overflow: hidden;
        }}
        [data-testid="stDataFrame"] [role="columnheader"],
        [data-testid="stDataEditor"] [role="columnheader"],
        [data-testid="stDataFrame"] thead th,
        [data-testid="stTable"] thead th {{
            background: var(--polar-blue) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}
        [data-testid="stDataFrame"] [role="columnheader"] *,
        [data-testid="stDataEditor"] [role="columnheader"] *,
        [data-testid="stDataFrame"] thead th *,
        [data-testid="stTable"] thead th * {{ color: #FFFFFF !important; fill: #FFFFFF !important; }}
        [data-testid="stForm"] {{
            background: #FFFFFF;
            border: 1px solid var(--polar-border);
            border-radius: 8px;
            padding: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str, month: date | None = None):
    """Exibe o cabeçalho editorial compartilhado pelas páginas."""
    period = f" · {MONTHS[month.month].upper()} {month.year}" if month else ""
    st.markdown(
        f'<div class="polar-kicker">CAMPANHA POLAR{period}</div>'
        f'<h1 class="polar-page-title">{title}</h1>'
        f'<p class="polar-page-subtitle">{subtitle}</p>',
        unsafe_allow_html=True,
    )


def format_currency_br(value: float) -> str:
    """Formata um total monetário sem depender do locale do servidor."""
    formatted = f"{value:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"


def format_percentage_br(value: float) -> str:
    """Formata percentuais da interface sem alterar a precisão usada no XP."""
    return f"{value:,.1f}%".replace(",", "_").replace(".", ",").replace("_", ".")


def campaign_classification(xp: float) -> str:
    """Traduz o XP acumulado para a faixa de classificação da campanha."""
    # Os limites superiores são inclusivos conforme o regulamento. Na prática,
    # os eventos atuais geram XP inteiro, mas a função aceita float para manter o
    # contrato das consolidações com pandas.
    if xp < 370:
        return "Sem classificação"
    if xp <= 500:
        return "Bronze"
    if xp <= 800:
        return "Prata"
    if xp <= 1_039:
        return "Ouro"
    if xp <= 1_200:
        return "Diamante"
    return "Polar"


def build_budget_card_html(budget: dict) -> str:
    """Monta o cartão visual do budget sem interpretar `R$` como Markdown."""
    attainment = float(budget["atingimento_pct"])
    # O percentual textual pode superar 100% ou ficar negativo. Somente a barra
    # é limitada ao intervalo visual válido para não quebrar o layout.
    bar_width = min(max(attainment, 0.0), 100.0)
    reference = date.fromisoformat(str(budget["data_referencia"]))
    return f"""
        <div class="polar-budget-card">
            <div class="polar-budget-grid">
                <div>
                    <span class="polar-budget-label">Atingimento</span>
                    <span class="polar-budget-percentage">{escape(format_percentage_br(attainment))}</span>
                </div>
                <div>
                    <span class="polar-budget-label">Realizado elegível</span>
                    <span class="polar-budget-value">{escape(format_currency_br(float(budget['realizado'])))}</span>
                </div>
                <div>
                    <span class="polar-budget-label">Budget anual</span>
                    <span class="polar-budget-value">{escape(format_currency_br(float(budget['budget'])))}</span>
                </div>
            </div>
            <div class="polar-budget-track" aria-label="Atingimento do budget">
                <div class="polar-budget-fill" style="width: {bar_width:.4f}%"></div>
            </div>
            <div class="polar-budget-reference">
                Realizado elegível de 2026 até {reference:%d/%m/%Y}.
            </div>
        </div>
    """


def indicator_xp_by_region(rows: list[dict], seller_cap: float | None = None) -> dict[str, float]:
    """Soma XP por região, aplicando antes o teto acumulado de cada vendedor."""
    if seller_cap is None:
        totals: dict[str, float] = {}
        for row in rows:
            region = str(row.get("regiao") or "").strip()
            if region:
                totals[region] = totals.get(region, 0.0) + float(row.get("xp") or 0)
        return totals

    # Novos e reativados têm teto individual. Primeiro acumulamos por vendedor
    # e região e só depois somamos os valores limitados na região. Isso preserva
    # o teto de cada participante em eventos divididos 50/50.
    seller_totals: dict[tuple[str, str], float] = {}
    for row in rows:
        region = str(row.get("regiao") or "").strip()
        seller = str(row.get("vendedor") or "Não identificado").strip()
        if region:
            key = (region, seller)
            seller_totals[key] = seller_totals.get(key, 0.0) + float(row.get("xp") or 0)
    totals: dict[str, float] = {}
    for (region, _seller), xp in seller_totals.items():
        totals[region] = totals.get(region, 0.0) + min(xp, seller_cap)
    return totals


def build_xp_overview_frame(
    advancement_by_month: dict[date, list[dict]],
    new_customers: list[dict],
    reactivated_customers: list[dict],
    product_mix: list[dict],
    sales_results: list[dict],
) -> pd.DataFrame:
    """Consolida os cinco indicadores no grão regional."""
    # Adiantamento e vendas já pertencem à região. Novos, reativados e mix são
    # eventos de vendedores que precisam ser agregados para a visão regional.
    advancement_xp: dict[str, float] = {}
    regions: set[str] = set()
    for rows in advancement_by_month.values():
        for row in rows:
            region = str(row.get("regiao") or "").strip()
            if not region:
                continue
            regions.add(region)
            advancement_xp[region] = advancement_xp.get(region, 0.0) + 10 * sum(
                bool(row.get(field)) for field in FIELDS
            )

    new_xp = indicator_xp_by_region(new_customers, seller_cap=100)
    reactivated_xp = indicator_xp_by_region(reactivated_customers, seller_cap=80)
    mix_xp = indicator_xp_by_region(product_mix)
    sales_xp = {
        str(row.get("regiao") or "").strip(): float(row.get("xp") or 0)
        for row in sales_results
        if str(row.get("regiao") or "").strip()
    }
    regions.update(new_xp)
    regions.update(reactivated_xp)
    regions.update(mix_xp)
    regions.update(sales_xp)

    # A união das chaves impede que uma região desapareça apenas porque ainda
    # não pontuou em um dos indicadores.
    records = []
    for region in sorted(regions):
        values = {
            "XP por cliente novo": new_xp.get(region, 0.0),
            "XP por cliente reativado": reactivated_xp.get(region, 0.0),
            "XP por expansão de mix": mix_xp.get(region, 0.0),
            "XP por atingimento de meta": sales_xp.get(region, 0.0),
            "XP por adiantamento": advancement_xp.get(region, 0.0),
        }
        total_xp = sum(values.values())
        records.append({
            "Região": region,
            "Classificação": campaign_classification(total_xp),
            **values,
            "XP total": total_xp,
        })
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    return frame.sort_values(
        ["XP total", "Região"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)


def build_individual_new_customers_frame(rows: list[dict], region: str) -> pd.DataFrame:
    """Prepara os eventos de clientes novos da região selecionada."""
    columns = [
        "Data", "Grupo comercial", "Pedido de venda", "Vendedores", "Região",
        "Segmento", "Atribuição", "XP",
    ]
    frame = pd.DataFrame([
        row for row in rows if str(row.get("regiao") or "").strip() == region
    ])
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame["data_primeira_compra"] = pd.to_datetime(
        frame["data_primeira_compra"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    frame["pedidos"] = frame["pedidos"].map(format_sales_orders)
    frame = frame.rename(columns={
        "nome_grupo_comercial": "Grupo comercial",
        "data_primeira_compra": "Data",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "situacao_atribuicao": "Atribuição",
        "xp": "XP",
    })
    return frame[columns]


def build_individual_reactivated_customers_frame(
    rows: list[dict], region: str,
) -> pd.DataFrame:
    """Prepara os eventos de clientes reativados da região selecionada."""
    columns = [
        "Data", "Última compra", "Prazo", "Grupo comercial", "Pedido de venda",
        "Vendedores", "Região", "Segmento", "Atribuição", "XP",
    ]
    frame = pd.DataFrame([
        row for row in rows if str(row.get("regiao") or "").strip() == region
    ])
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame["data_reativacao"] = pd.to_datetime(
        frame["data_reativacao"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    frame["data_ultima_compra"] = pd.to_datetime(
        frame["data_ultima_compra"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    frame["prazo_meses"] = frame["prazo_meses"].map(lambda value: f"{value} meses")
    frame["pedidos"] = frame["pedidos"].map(format_sales_orders)
    frame = frame.rename(columns={
        "nome_grupo_comercial": "Grupo comercial",
        "data_reativacao": "Data",
        "data_ultima_compra": "Última compra",
        "prazo_meses": "Prazo",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "situacao_atribuicao": "Atribuição",
        "xp": "XP",
    })
    return frame[columns]


def build_individual_product_mix_frame(rows: list[dict], region: str) -> pd.DataFrame:
    """Prepara todas as compras de mix da região, elegíveis ou não."""
    columns = [
        "Data da compra", "Primeira compra da família", "Grupo comercial", "Família",
        "Produtos", "Pedido de venda", "Vendedores", "Região", "Segmento",
        "Valor da linha", "Mínimo", "Resultado", "XP",
    ]
    frame = pd.DataFrame([
        row for row in rows if str(row.get("regiao") or "").strip() == region
    ])
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame["data_expansao"] = pd.to_datetime(
        frame["data_expansao"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    frame["data_primeira_compra_familia"] = pd.to_datetime(
        frame["data_primeira_compra_familia"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    frame["pedidos"] = frame["pedidos"].map(format_sales_orders)
    frame = frame.rename(columns={
        "data_expansao": "Data da compra",
        "data_primeira_compra_familia": "Primeira compra da família",
        "nome_grupo_comercial": "Grupo comercial",
        "grupo_mix": "Família",
        "produtos": "Produtos",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "valor_linha_elegivel": "Valor da linha",
        "valor_minimo": "Mínimo",
        "situacao_evento": "Resultado",
        "xp": "XP",
    })
    return frame[columns]


def build_individual_sales_frame(sales_results: list[dict], region: str) -> pd.DataFrame:
    """Prepara o resultado acumulado de venda e meta da região."""
    columns = [
        "Região", "Vendedores", "Realizado acumulado", "Meta acumulada até hoje",
        "Atingimento acumulado", "XP da região", "Meta diária atual",
    ]
    frame = pd.DataFrame([
        row for row in sales_results if str(row.get("regiao") or "").strip() == region
    ])
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.rename(columns={
        "regiao": "Região",
        "vendedores": "Vendedores",
        "realizado_acumulado": "Realizado acumulado",
        "meta_acumulada_ate_data": "Meta acumulada até hoje",
        "atingimento_acumulado_pct": "Atingimento acumulado",
        "xp": "XP da região",
        "meta_diaria_mes_atual": "Meta diária atual",
    })
    for column in (
        "Realizado acumulado", "Meta acumulada até hoje",
        "Atingimento acumulado", "Meta diária atual",
    ):
        frame[column] = frame[column].map(
            lambda value: float(value) if value is not None else None
        )
    return frame[columns]


def build_individual_advancement_frame(
    advancement_by_month: dict[date, list[dict]], region: str,
) -> pd.DataFrame:
    """Lista as confirmações mensais de adiantamento da região."""
    columns = [
        "Mês", "1ª semana - 32%", "2ª semana - 56%", "3ª semana - 80%",
        "XP", "Observações",
    ]
    records = []
    for month, rows in sorted(advancement_by_month.items()):
        source = next(
            (row for row in rows if str(row.get("regiao") or "").strip() == region),
            None,
        )
        if source is None:
            continue
        checks = {field: bool(source.get(field)) for field in FIELDS}
        records.append({
            "Mês": f"{MONTHS[month.month]} {month.year}",
            "1ª semana - 32%": checks["semana_1_32"],
            "2ª semana - 56%": checks["semana_2_56"],
            "3ª semana - 80%": checks["semana_3_80"],
            "XP": 10 * sum(checks.values()),
            "Observações": str(source.get("observacao") or ""),
        })
    return pd.DataFrame(records, columns=columns)


def build_new_customers_region_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Resume as linhas de atribuição dos clientes novos por região."""
    records = [
        row for row in frame.to_dict("records") if str(row["regiao"]).strip()
    ]

    if not records:
        return pd.DataFrame(columns=[
            "Região", "Quantidade de clientes novos", "Lista dos clientes novos", "Total XP",
        ])

    summary = []
    regional = pd.DataFrame(records)
    for region, rows in regional.groupby("regiao", sort=True):
        clients = {
            row["grupo_comercial_id"]: row["nome_grupo_comercial"]
            for row in rows.to_dict("records")
        }
        summary.append({
            "Região": region,
            "Quantidade de clientes novos": len(clients),
            "Lista dos clientes novos": "\n".join(
                sorted(clients.values(), key=str.casefold)
            ),
            "Total XP": float(rows["xp"].sum()),
        })
    return pd.DataFrame(summary)


def build_reactivated_customers_region_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Resume as linhas de atribuição dos clientes reativados por região."""
    records = [
        row for row in frame.to_dict("records") if str(row["regiao"]).strip()
    ]
    columns = [
        "Região",
        "Quantidade de clientes reativados",
        "Lista dos clientes reativados",
        "Total XP",
    ]
    if not records:
        return pd.DataFrame(columns=columns)

    summary = []
    regional = pd.DataFrame(records)
    for region, rows in regional.groupby("regiao", sort=True):
        clients = {
            row["grupo_comercial_id"]: row["nome_grupo_comercial"]
            for row in rows.to_dict("records")
        }
        summary.append({
            "Região": region,
            "Quantidade de clientes reativados": len(clients),
            "Lista dos clientes reativados": "\n".join(
                sorted(clients.values(), key=str.casefold)
            ),
            "Total XP": float(rows["xp"].sum()),
        })
    return pd.DataFrame(summary, columns=columns)


def build_product_mix_region_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Resume as expansões de mix confirmadas por região."""
    # Ao contrário de novos/reativados, o resumo de mix mostra apenas eventos
    # efetivamente pontuados; os demais permanecem disponíveis no detalhe.
    confirmed = frame[(frame["xp"] > 0) & frame["regiao"].astype(str).str.strip().ne("")]
    columns = [
        "Região", "Quantidade de expansões", "Lista das expansões", "Total XP",
    ]
    if confirmed.empty:
        return pd.DataFrame(columns=columns)

    summary = []
    for region, rows in confirmed.groupby("regiao", sort=True):
        expansions = {
            (row["grupo_comercial_id"], row["grupo_mix"]): (
                f"{row['nome_grupo_comercial']} — {row['grupo_mix']}"
            )
            for row in rows.to_dict("records")
        }
        summary.append({
            "Região": region,
            "Quantidade de expansões": len(expansions),
            "Lista das expansões": "\n".join(
                sorted(expansions.values(), key=str.casefold)
            ),
            "Total XP": float(rows["xp"].sum()),
        })
    return pd.DataFrame(summary, columns=columns)


def build_region_summary_html(summary: pd.DataFrame, list_column: str) -> str:
    """Monta uma linha por região e preserva cada item da lista em sua própria linha."""
    columns = list(summary.columns)
    header = "".join(f"<th scope='col'>{escape(str(column))}</th>" for column in columns)
    body = []
    for record in summary.to_dict("records"):
        items = str(record.get(list_column) or "").splitlines() or [""]
        items_html = "".join(
            f"<div class='polar-summary-item'>{escape(item)}</div>" for item in items
        )
        count = int(record[columns[1]])
        xp = f"{float(record[columns[3]]):g} XP"
        body.append(
            "<tr>"
            f"<td>{escape(str(record[columns[0]]))}</td>"
            f"<td class='polar-summary-number'>{count}</td>"
            f"<td>{items_html}</td>"
            f"<td class='polar-summary-number'>{escape(xp)}</td>"
            "</tr>"
        )
    if not body:
        body.append("<tr><td colspan='4'>Nenhum registro confirmado.</td></tr>")
    return (
        "<style>"
        ".polar-summary-wrap{overflow-x:auto;border:1px solid var(--polar-border);"
        "border-radius:10px;margin:.25rem 0 1rem;background:#fff}"
        ".polar-summary-table{border-collapse:collapse;table-layout:fixed;width:100%;"
        "min-width:800px;color:var(--polar-ink);font-size:.93rem}"
        ".polar-summary-table th{background:#f7f9fc;color:#5c6f86;font-weight:500;"
        "text-align:left}"
        ".polar-summary-table th,.polar-summary-table td{border-bottom:1px solid "
        "var(--polar-border);border-right:1px solid var(--polar-border);padding:.75rem;"
        "vertical-align:middle}"
        ".polar-summary-table th:nth-child(1){width:17%}"
        ".polar-summary-table th:nth-child(2){width:25%}"
        ".polar-summary-table th:nth-child(3){width:45%}"
        ".polar-summary-table th:nth-child(4){width:13%}"
        ".polar-summary-table th:last-child,.polar-summary-table td:last-child{border-right:0}"
        ".polar-summary-table tbody tr:last-child td{border-bottom:0}"
        ".polar-summary-number{text-align:right;white-space:nowrap}"
        ".polar-summary-item{line-height:1.55;overflow-wrap:anywhere}"
        "</style>"
        "<div class='polar-summary-wrap'><table class='polar-summary-table'>"
        f"<thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def render_region_summary_table(summary: pd.DataFrame, list_column: str):
    st.markdown(build_region_summary_html(summary, list_column), unsafe_allow_html=True)


def format_sales_orders(value: object) -> str:
    """Oculta a filial padrão na exibição e preserva pedidos de outras filiais."""
    # A transformação é apenas visual. A chave técnica no banco continua sendo
    # filial + pedido, inclusive para evitar colisão entre filiais.
    return str(value or "").replace("01101/", "")


def validate_customer_detail_contract(
    frame: pd.DataFrame,
    required_columns: set[str],
    sql_filename: str,
) -> bool:
    """Evita falha quando o app e a função RPC ainda estão em versões diferentes."""
    missing = required_columns.difference(frame.columns)
    if not missing:
        return True
    st.warning(
        "Esta página recebeu o formato anterior dos dados. Reinicie o aplicativo no "
        f"Streamlit Cloud e execute novamente `sql/{sql_filename}` no Supabase."
    )
    return False


def configuration():
    """Lê a configuração pública necessária para Auth e Data API."""
    try:
        supabase_url = str(st.secrets["SUPABASE_URL"])
        publishable_key = str(st.secrets["SUPABASE_PUBLISHABLE_KEY"])
        return SupabaseAuthenticator(supabase_url, publishable_key)
    except (KeyError, FileNotFoundError, ValueError):
        # Interromper aqui é mais seguro que abrir o painel parcialmente ou
        # tentar operar com uma credencial administrativa indevida.
        render_page_header(
            "Campanha Polar",
            "O painel está pronto para receber a conexão segura com os dados comerciais.",
        )
        st.info("O painel está aguardando a configuração do Supabase.")
        st.caption("A configuração está descrita no README do projeto.")
        st.stop()


def current_identity(authenticator: SupabaseAuthenticator):
    """Revalida a sessão e devolve identidade e cliente autenticado da Data API."""
    saved_session = st.session_state.get("supabase_auth_session")
    if not isinstance(saved_session, dict):
        raise PermissionDenied("Faça login para acessar o painel.")
    # A identidade nunca é confiada apenas ao session_state: o Supabase valida
    # os tokens e devolve os tokens renovados antes de qualquer consulta.
    refreshed_session, client = authenticator.authenticated_client(saved_session)
    st.session_state["supabase_auth_session"] = refreshed_session
    return Identity.from_authenticated_user(refreshed_session), client


def render_login(authenticator: SupabaseAuthenticator):
    """Exibe a entrada por e-mail e senha do Supabase Auth."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 520px; padding-top: 14vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH), width=210)
    render_page_header("Campanha Polar", "Entre com seu e-mail e senha para continuar.")
    with st.form("supabase_login"):
        email = st.text_input("E-mail", autocomplete="email")
        password = st.text_input("Senha", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Entrar", type="primary", width="stretch")
    if submitted:
        try:
            session = authenticator.sign_in(email, password)
        except AuthenticationServiceError:
            st.error("Não foi possível acessar o serviço de autenticação. Tente novamente.")
        else:
            if session is None:
                st.error("E-mail ou senha inválidos.")
            else:
                st.session_state["supabase_auth_session"] = session
                st.rerun()


def render_sidebar(
    identity: Identity,
    authenticator: SupabaseAuthenticator,
    updated_at: datetime | None = None,
):
    """Renderiza navegação e conta conectada."""
    with st.sidebar:
        st.caption("NAVEGAÇÃO")
        page = st.radio(
            "Página",
            (
                "Visão geral",
                "Análise individual",
                "Venda no Quadrimestre",
                "Clientes novos",
                "Clientes reativados",
                "Mix de produtos",
                "Adiantamento de meta",
            ),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Usuário conectado")
        st.write(identity.email)
        access = "Pode editar o adiantamento" if identity.can_edit else "Acesso para consulta"
        st.caption(access)
        st.divider()
        st.caption("ÚLTIMA ATUALIZAÇÃO DOS DADOS")
        if updated_at is None:
            st.write("Não disponível")
        else:
            st.write(f"{updated_at:%d/%m/%Y às %H:%M:%S}")
        if st.button("Sair", key="polar_logout", width="stretch"):
            saved_session = st.session_state.get("supabase_auth_session", {})
            try:
                authenticator.sign_out(saved_session)
            except AuthenticationServiceError:
                pass
            st.session_state.clear()
            st.rerun()
    return page


def render_overview(
    advancement_repository: Repository,
    new_customers_repository: NewCustomersRepository,
    reactivated_customers_repository: ReactivatedCustomersRepository,
    product_mix_repository: ProductMixRepository,
    sales_repository: SalesRepository,
    budget_repository: BudgetRepository,
    reference: date | None = None,
):
    """Exibe o budget anual e os XP consolidados por região."""
    reference = reference or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    render_page_header(
        "Visão geral",
        "Acompanhe o budget anual de vendas e o XP consolidado de cada região.",
    )
    budget = budget_repository.load()
    st.subheader("Atingimento do budget anual de vendas")
    st.markdown(build_budget_card_html(budget), unsafe_allow_html=True)

    # Cada fonte é recalculada pela situação corrente. Não há fotografia local
    # persistida do ranking, portanto correções retroativas aparecem no rerun.
    advancement_by_month = advancement_repository.load_campaign()
    rows_by_month = sales_repository.load_through(reference)
    available_sales = {month: rows for month, rows in rows_by_month.items() if rows}
    sales_results = (
        calculate_cumulative_region_results(available_sales, reference)
        if available_sales else []
    )
    frame = build_xp_overview_frame(
        advancement_by_month,
        new_customers_repository.load(),
        reactivated_customers_repository.load(),
        product_mix_repository.load(),
        sales_results,
    )

    st.subheader("XP por região")
    if frame.empty:
        st.info("Nenhuma região participante está disponível para a campanha.")
        return
    st.dataframe(
        frame,
        column_config={
            column: st.column_config.NumberColumn(column, format="%.0f XP")
            for column in frame.columns
            if column not in {"Região", "Classificação"}
        },
        hide_index=True,
        width="stretch",
    )


def render_individual_analysis(
    advancement_repository: Repository,
    new_customers_repository: NewCustomersRepository,
    reactivated_customers_repository: ReactivatedCustomersRepository,
    product_mix_repository: ProductMixRepository,
    sales_repository: SalesRepository,
    reference: date | None = None,
):
    """Exibe o resultado completo de uma região e os eventos que formam seu XP."""
    reference = reference or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    render_page_header(
        "Análise individual",
        "Selecione uma região para conferir seu XP e todos os resultados da campanha.",
    )

    # A página usa exatamente as mesmas fontes e consolidação da Visão geral;
    # isso evita divergência entre o ranking e o detalhe selecionado.
    advancement_by_month = advancement_repository.load_campaign()
    new_customers = new_customers_repository.load()
    reactivated_customers = reactivated_customers_repository.load()
    product_mix = product_mix_repository.load()
    rows_by_month = sales_repository.load_through(reference)
    available_sales = {month: rows for month, rows in rows_by_month.items() if rows}
    sales_results = (
        calculate_cumulative_region_results(available_sales, reference)
        if available_sales else []
    )
    overview = build_xp_overview_frame(
        advancement_by_month,
        new_customers,
        reactivated_customers,
        product_mix,
        sales_results,
    )
    if overview.empty:
        st.info("Nenhuma região participante está disponível para a campanha.")
        return

    selected_region = st.selectbox(
        "Região",
        overview["Região"].tolist(),
        key="individual_analysis_region",
    )
    regional = overview[overview["Região"] == selected_region].iloc[0]

    total_column, classification_column = st.columns(2)
    total_column.metric("XP total", f"{float(regional['XP total']):g} XP")
    classification_column.metric("Classificação", regional["Classificação"])

    components = [
        ("Clientes novos", "XP por cliente novo"),
        ("Clientes reativados", "XP por cliente reativado"),
        ("Expansão de mix", "XP por expansão de mix"),
        ("Atingimento de meta", "XP por atingimento de meta"),
        ("Adiantamento", "XP por adiantamento"),
    ]
    st.subheader("Composição do XP")
    metric_columns = st.columns(len(components))
    chart_records = []
    for metric_column, (label, source_column) in zip(metric_columns, components):
        xp = float(regional[source_column])
        metric_column.metric(label, f"{xp:g} XP")
        chart_records.append({"Indicador": label, "XP": xp})
    st.bar_chart(
        pd.DataFrame(chart_records).set_index("Indicador"),
        color=POLAR_BLUE,
        horizontal=True,
        sort=False,
        height=280,
    )
    st.caption(
        "Os totais de clientes novos e reativados já consideram os tetos acumulados por "
        "vendedor. As tabelas abaixo preservam cada evento para conferência."
    )

    new_detail = build_individual_new_customers_frame(new_customers, selected_region)
    reactivated_detail = build_individual_reactivated_customers_frame(
        reactivated_customers, selected_region
    )
    mix_detail = build_individual_product_mix_frame(product_mix, selected_region)
    sales_detail = build_individual_sales_frame(sales_results, selected_region)
    advancement_detail = build_individual_advancement_frame(
        advancement_by_month, selected_region
    )

    st.subheader("Detalhamento da região")
    new_tab, reactivated_tab, mix_tab, sales_tab, advancement_tab = st.tabs([
        "Clientes novos",
        "Clientes reativados",
        "Expansão de mix",
        "Venda x meta",
        "Adiantamento",
    ])
    with new_tab:
        if new_detail.empty:
            st.info("A região não possui clientes novos na campanha.")
        else:
            st.dataframe(
                new_detail,
                column_config={
                    "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
                },
                hide_index=True,
                width="stretch",
            )
    with reactivated_tab:
        if reactivated_detail.empty:
            st.info("A região não possui clientes reativados na campanha.")
        else:
            st.dataframe(
                reactivated_detail,
                column_config={
                    "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
                },
                hide_index=True,
                width="stretch",
            )
    with mix_tab:
        st.caption(
            "A tabela mostra todas as compras das famílias acompanhadas e explica se cada "
            "uma foi elegível para XP."
        )
        if mix_detail.empty:
            st.info("A região não possui compras dos produtos de mix na campanha.")
        else:
            st.dataframe(
                mix_detail,
                column_config={
                    "Valor da linha": st.column_config.NumberColumn(
                        "Valor da linha", format="R$ %.2f"
                    ),
                    "Mínimo": st.column_config.NumberColumn("Mínimo", format="R$ %.2f"),
                    "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
                },
                hide_index=True,
                width="stretch",
            )
    with sales_tab:
        st.caption(f"Resultado acumulado até {reference:%d/%m/%Y}.")
        if sales_detail.empty:
            st.info("A região ainda não possui venda e meta acumuladas disponíveis.")
        else:
            st.dataframe(
                sales_detail,
                column_config={
                    "Realizado acumulado": st.column_config.NumberColumn(
                        "Realizado acumulado", format="R$ %.2f"
                    ),
                    "Meta acumulada até hoje": st.column_config.NumberColumn(
                        "Meta acumulada até hoje", format="R$ %.2f"
                    ),
                    "Atingimento acumulado": st.column_config.NumberColumn(
                        "Atingimento acumulado", format="%.1f%%"
                    ),
                    "XP da região": st.column_config.NumberColumn(
                        "XP da região", format="%.0f XP"
                    ),
                    "Meta diária atual": st.column_config.NumberColumn(
                        "Meta diária atual", format="R$ %.2f"
                    ),
                },
                hide_index=True,
                width="stretch",
            )
    with advancement_tab:
        if advancement_detail.empty:
            st.info("A região não possui registros de adiantamento na campanha.")
        else:
            st.dataframe(
                advancement_detail,
                column_config={
                    "1ª semana - 32%": st.column_config.CheckboxColumn(
                        "1ª semana - 32%", disabled=True
                    ),
                    "2ª semana - 56%": st.column_config.CheckboxColumn(
                        "2ª semana - 56%", disabled=True
                    ),
                    "3ª semana - 80%": st.column_config.CheckboxColumn(
                        "3ª semana - 80%", disabled=True
                    ),
                    "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
                },
                hide_index=True,
                width="stretch",
            )


def render_quadrimester_sales(repository: SalesRepository, reference: date | None = None):
    """Exibe o acumulado do quadrimestre até o mês e o dia de referência."""
    reference = reference or datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    rows_by_month = repository.load_through(reference)
    requested_month = max(rows_by_month)
    # Metas futuras não são estimadas. Meses sem linhas são removidos e a tela
    # informa que o acumulado termina na última competência publicada.
    available_rows = {month: rows for month, rows in rows_by_month.items() if rows}
    current_month = max(available_rows) if available_rows else requested_month
    render_page_header(
        "Venda no Quadrimestre",
        "Compare as vendas acumuladas com as metas do quadrimestre disponíveis até hoje.",
        current_month,
    )
    if not available_rows:
        st.info("Ainda não há metas disponíveis para as regiões participantes.")
        return
    if current_month < requested_month:
        st.warning(
            f"A meta de {MONTHS[requested_month.month].lower()} ainda não está disponível. "
            f"O acumulado abaixo termina em {MONTHS[current_month.month].lower()}."
        )

    results = calculate_cumulative_region_results(available_rows, reference)
    frame = pd.DataFrame(results)
    elapsed = int(frame.iloc[0]["dias_uteis_decorridos"])
    total_days = int(frame.iloc[0]["dias_uteis_mes"])
    remaining = int(frame.iloc[0]["dias_uteis_restantes"])

    total_published_goals = sum(frame["metas_publicadas"])
    total_partial = sum(frame["meta_acumulada_ate_data"])
    total_realized = sum(frame["realizado_acumulado"])
    total_attainment = (
        total_realized * 100 / total_partial if total_partial else None
    )

    current_month_note = (
        f"{MONTHS[current_month.month]} entra proporcionalmente aos {elapsed} de "
        f"{total_days} dias úteis decorridos, com {remaining} restantes."
    )
    if current_month == min(available_rows):
        period_note = current_month_note
    else:
        period_note = f"Os meses anteriores entram completos; {current_month_note.lower()}"
    st.caption(f"Referência: {reference:%d/%m/%Y}. {period_note}")
    metric_goal, metric_partial, metric_realized, metric_attainment, metric_days = st.columns(5)
    metric_goal.metric(
        f"Metas publicadas até {MONTHS[current_month.month].lower()}",
        format_currency_br(float(total_published_goals)),
    )
    metric_partial.metric("Meta acumulada até hoje", format_currency_br(float(total_partial)))
    metric_realized.metric("Realizado acumulado", format_currency_br(float(total_realized)))
    metric_attainment.metric(
        "Atingimento acumulado",
        format_percentage_br(float(total_attainment)) if total_attainment is not None else "Pendente",
    )
    metric_days.metric("Dias úteis", f"{elapsed} de {total_days}")

    st.subheader("Venda x meta por região")
    st.caption(
        "O percentual exato, antes da formatação visual, define o XP. O resultado e o XP "
        "permanecem únicos por região e acumulam os meses decorridos; a coluna Vendedores "
        "mostra quem compôs suas vendas."
    )
    display = frame.copy()
    display = display.rename(columns={
        "regiao": "Região",
        "vendedores": "Vendedores",
        "realizado_acumulado": "Realizado acumulado",
        "meta_acumulada_ate_data": "Meta acumulada até hoje",
        "atingimento_acumulado_pct": "Atingimento acumulado",
        "xp": "XP da região",
        "meta_diaria_mes_atual": "Meta diária atual",
    })
    numeric_columns = [
        "Realizado acumulado", "Meta acumulada até hoje", "Atingimento acumulado",
        "Meta diária atual",
    ]
    for column in numeric_columns:
        display[column] = display[column].map(
            lambda value: float(value) if value is not None else None
        )
    st.dataframe(
        display[[
            "Região", "Vendedores", "Realizado acumulado", "Meta acumulada até hoje",
            "Atingimento acumulado", "XP da região", "Meta diária atual",
        ]],
        column_config={
            "Realizado acumulado": st.column_config.NumberColumn(
                "Realizado acumulado", format="R$ %.2f"
            ),
            "Meta acumulada até hoje": st.column_config.NumberColumn(
                "Meta acumulada até hoje", format="R$ %.2f"
            ),
            "Atingimento acumulado": st.column_config.NumberColumn(
                "Atingimento acumulado", format="%.1f%%"
            ),
            "XP da região": st.column_config.NumberColumn("XP da região", format="%d XP"),
            "Meta diária atual": st.column_config.NumberColumn(
                "Meta diária atual", format="R$ %.2f"
            ),
        },
        hide_index=True,
        width="stretch",
    )


def render_new_customers(repository: NewCustomersRepository):
    """Exibe os primeiros eventos de compra identificados no histórico desde 2022."""
    render_page_header(
        "Clientes novos",
        "Acompanhe os grupos em sua primeira compra elegível e a atribuição dos XP.",
    )
    rows = repository.load()
    if not rows:
        st.info("Nenhum cliente novo foi identificado na campanha.")
        return

    frame = pd.DataFrame(rows)
    if not validate_customer_detail_contract(
        frame,
        {"grupo_comercial_id", "nome_grupo_comercial", "data_primeira_compra", "pedidos",
         "vendedor", "regiao", "segmento", "situacao_atribuicao", "xp"},
        "clientes_novos.sql",
    ):
        return
    st.subheader("Resumo por região")
    st.caption(
        "Cada grupo comercial é contado uma vez em cada região participante. Em eventos com "
        "duas regiões, o XP é dividido entre elas."
    )
    summary = build_new_customers_region_summary(frame)
    render_region_summary_table(summary, "Lista dos clientes novos")

    st.subheader("Detalhamento dos clientes")
    region_names = sorted({
        str(region).strip() for region in frame["regiao"] if str(region).strip()
    })
    selected_region = st.selectbox("Região", ["Todas", *region_names])

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regiao"] == selected_region]

    st.caption(
        "Cada linha representa a atribuição de um vendedor. Pedidos triangulados aparecem em "
        "duas linhas, uma para cada vendedor e região."
    )
    display = filtered.copy()
    first_purchase = pd.to_datetime(display["data_primeira_compra"], errors="coerce")
    display["data_primeira_compra"] = first_purchase.dt.strftime("%d/%m/%Y")
    display["pedidos"] = display["pedidos"].map(format_sales_orders)
    display = display.rename(columns={
        "nome_grupo_comercial": "Grupo comercial",
        "data_primeira_compra": "Data",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "situacao_atribuicao": "Atribuição",
        "xp": "XP",
    })
    st.dataframe(
        display[[
            "Data", "Grupo comercial", "Pedido de venda", "Vendedores", "Região",
            "Segmento", "Atribuição", "XP",
        ]],
        column_config={
            "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
        },
        hide_index=True,
        width="stretch",
    )


def render_reactivated_customers(repository: ReactivatedCustomersRepository):
    """Exibe retornos após 6 meses em Canais ou 12 meses em Construção."""
    render_page_header(
        "Clientes reativados",
        "Acompanhe os grupos que voltaram a comprar após o período mínimo de inatividade.",
    )
    rows = repository.load()
    if not rows:
        st.info("Nenhum cliente reativado foi identificado na campanha.")
        return

    frame = pd.DataFrame(rows)
    if not validate_customer_detail_contract(
        frame,
        {"grupo_comercial_id", "nome_grupo_comercial", "data_reativacao",
         "data_ultima_compra", "prazo_meses", "pedidos", "vendedor", "regiao",
         "segmento", "situacao_atribuicao", "xp"},
        "clientes_reativados.sql",
    ):
        return
    st.subheader("Resumo por região")
    st.caption(
        "Cada grupo comercial é contado uma vez em cada região participante. O XP das duas "
        "linhas de uma triangulação é somado na respectiva região."
    )
    summary = build_reactivated_customers_region_summary(frame)
    render_region_summary_table(summary, "Lista dos clientes reativados")

    st.subheader("Detalhamento dos clientes")
    region_names = sorted({
        str(region).strip() for region in frame["regiao"] if str(region).strip()
    })
    selected_region = st.selectbox(
        "Região", ["Todas", *region_names], key="reactivated_region"
    )

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regiao"] == selected_region]

    st.caption(
        "Cada linha representa a atribuição de um vendedor. Pedidos triangulados aparecem em "
        "duas linhas, uma para cada vendedor e região."
    )
    display = filtered.copy()
    activation = pd.to_datetime(display["data_reativacao"], errors="coerce")
    display["data_reativacao"] = activation.dt.strftime("%d/%m/%Y")
    display["pedidos"] = display["pedidos"].map(format_sales_orders)
    display["data_ultima_compra"] = pd.to_datetime(
        display["data_ultima_compra"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    display["prazo_meses"] = display["prazo_meses"].map(lambda value: f"{value} meses")
    display = display.rename(columns={
        "nome_grupo_comercial": "Grupo comercial",
        "data_reativacao": "Data",
        "data_ultima_compra": "Última compra",
        "prazo_meses": "Prazo",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "situacao_atribuicao": "Atribuição",
        "xp": "XP",
    })
    st.dataframe(
        display[[
            "Data", "Última compra", "Prazo", "Grupo comercial", "Pedido de venda",
            "Vendedores", "Região", "Segmento", "Atribuição", "XP",
        ]],
        column_config={
            "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
        },
        hide_index=True,
        width="stretch",
    )


def render_product_mix(repository: ProductMixRepository):
    """Exibe todas as compras das famílias de mix e sua elegibilidade."""
    render_page_header(
        "Mix de produtos",
        "Acompanhe todas as compras das famílias mapeadas e entenda sua elegibilidade.",
    )
    rows = repository.load()
    if not rows:
        st.info("Nenhuma compra dos produtos de mix foi identificada na campanha.")
        return

    frame = pd.DataFrame(rows)
    if not validate_customer_detail_contract(
        frame,
        {"grupo_comercial_id", "nome_grupo_comercial", "data_expansao",
         "data_primeira_compra_familia", "grupo_mix", "produtos", "pedidos",
         "vendedor", "regiao", "segmento",
         "valor_linha_elegivel", "valor_minimo", "situacao_evento", "xp"},
        "mix_produtos.sql",
    ):
        return
    st.subheader("Resumo por região")
    st.caption(
        "O resumo considera somente expansões confirmadas. Cada combinação de grupo comercial "
        "e família é contada uma vez por região."
    )
    summary = build_product_mix_region_summary(frame)
    render_region_summary_table(summary, "Lista das expansões")

    st.subheader("Todas as compras dos produtos de mix")
    region_names = sorted({
        str(region).strip() for region in frame["regiao"] if str(region).strip()
    })
    selected_region = st.selectbox("Região", ["Todas", *region_names], key="mix_region")

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regiao"] == selected_region]

    st.caption(
        "Cada linha representa a atribuição de um vendedor. Pedidos triangulados aparecem em "
        "duas linhas. A coluna Resultado explica por que a compra é ou não elegível."
    )
    display = filtered.copy()
    event_date = pd.to_datetime(display["data_expansao"], errors="coerce")
    display["data_expansao"] = event_date.dt.strftime("%d/%m/%Y")
    display["data_primeira_compra_familia"] = pd.to_datetime(
        display["data_primeira_compra_familia"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    display["pedidos"] = display["pedidos"].map(format_sales_orders)
    display = display.rename(columns={
        "data_expansao": "Data da compra",
        "data_primeira_compra_familia": "Primeira compra da família",
        "nome_grupo_comercial": "Grupo comercial",
        "grupo_mix": "Família",
        "produtos": "Produtos",
        "pedidos": "Pedido de venda",
        "vendedor": "Vendedores",
        "regiao": "Região",
        "segmento": "Segmento",
        "valor_linha_elegivel": "Valor da linha",
        "valor_minimo": "Mínimo",
        "situacao_evento": "Resultado",
        "xp": "XP",
    })
    st.dataframe(
        display[[
            "Data da compra", "Primeira compra da família", "Grupo comercial", "Família",
            "Produtos", "Pedido de venda", "Vendedores", "Região", "Segmento",
            "Valor da linha", "Mínimo", "Resultado", "XP",
        ]],
        column_config={
            "Valor da linha": st.column_config.NumberColumn("Valor da linha", format="R$ %.2f"),
            "Mínimo": st.column_config.NumberColumn("Mínimo", format="R$ %.2f"),
            "XP": st.column_config.NumberColumn("XP", format="%.0f XP"),
        },
        hide_index=True,
        width="stretch",
    )


def advance_column(month: date, field: str) -> str:
    return f"m{month.month:02d}_{field}"


def advance_label(month: date, field: str) -> str:
    return f"{MONTH_ABBREVIATIONS[month.month]} | {ADVANCE_SUFFIXES[field]}"


def build_advancement_frame(month_rows: dict[date, list[dict]]) -> pd.DataFrame:
    """Transforma registros mensais em uma linha única por região."""
    # A API trabalha no grão região/mês; a tela pivota quatro meses e três fases
    # para oferecer os 12 checks em uma única linha por região.
    regions = sorted({row["regiao"] for rows in month_rows.values() for row in rows})
    records = []
    for region in regions:
        record = {"regiao": region}
        for month in month_rows:
            source = next((row for row in month_rows[month] if row["regiao"] == region), None)
            for field in FIELDS:
                record[advance_column(month, field)] = bool(source[field]) if source else False
        records.append(record)
    return pd.DataFrame(records)


def render_table(repository: Repository, identity: Identity, recheck_identity):
    """Renderiza os quatro meses em uma única tabela por região."""
    scope = f"campaign:{identity.user_id}"
    # O escopo inclui o ID do usuário para impedir que dados carregados por uma
    # sessão sejam reutilizados depois de uma troca de conta no mesmo navegador.
    if st.session_state.get("advance_scope") != scope:
        st.session_state["advance_month_rows"] = repository.load_campaign()
        st.session_state["advance_scope"] = scope
        st.session_state["advance_revision"] = st.session_state.get("advance_revision", 0) + 1
    month_rows = st.session_state["advance_month_rows"]
    frame = build_advancement_frame(month_rows)
    if frame.empty:
        st.info("Nenhuma região com meta positiva está disponível para a campanha.")
        return

    check_columns = [advance_column(month, field) for month in month_rows for field in FIELDS]
    checked = int(frame[check_columns].sum().sum())
    saved_rows = [row for rows in month_rows.values() for row in rows if row["versao"] > 0]
    a, b, c, d = st.columns(4)
    a.metric("Regiões", len(frame))
    b.metric("Atingimentos marcados", checked)
    c.metric("Registros mensais salvos", len(saved_rows))
    d.metric("XP de adiantamento", f"{checked * 10} XP")

    configs = {"regiao": st.column_config.TextColumn("Região", pinned=True)}
    for month in month_rows:
        for field in FIELDS:
            column = advance_column(month, field)
            configs[column] = st.column_config.CheckboxColumn(
                advance_label(month, field),
                help="Informe manualmente se a região atingiu esta fase.",
            )

    unavailable = [month for month, rows in month_rows.items() if not rows]
    disabled = ["regiao", *[
        advance_column(month, field)
        for month in unavailable
        for field in FIELDS
    ]]
    if unavailable:
        st.caption(
            "Aguardando metas para: "
            + ", ".join(MONTHS[month.month] for month in unavailable)
            + ". Os respectivos checks ficam desabilitados."
        )

    table_columns = ["regiao", *check_columns]
    if identity.can_edit:
        st.caption("Marque os atingimentos conferidos e salve a campanha inteira de uma vez.")
        with st.form("advance_form"):
            edited = st.data_editor(
                frame[table_columns],
                column_config=configs,
                disabled=disabled,
                num_rows="fixed",
                hide_index=True,
                width="stretch",
                key=f"advance_editor:{scope}:{st.session_state['advance_revision']}",
            )
            submitted = st.form_submit_button("Salvar alterações", type="primary", width="stretch")
        if submitted:
            # A identidade é conferida novamente imediatamente antes da escrita.
            # O banco ainda repetirá a autorização com o JWT da própria chamada.
            current, _ = recheck_identity()
            if current.user_id != identity.user_id:
                raise PermissionDenied("A conta conectada mudou. Recarregue a página.")
            edited_by_region = {row["regiao"]: row for row in edited.to_dict("records")}
            payload = []
            for month, rows in month_rows.items():
                for original in rows:
                    wide = edited_by_region[original["regiao"]]
                    payload.append({
                        "competencia": month,
                        "regiao": original["regiao"],
                        **{
                            field: bool(wide[advance_column(month, field)])
                            for field in FIELDS
                        },
                        "observacao": original["observacao"],
                        "versao": original["versao"],
                    })
            count = repository.save_campaign(payload, current)
            st.session_state.pop("advance_scope", None)
            st.session_state["advance_saved"] = (
                f"Dados salvos: {count} registro(s) mensal(is) atualizado(s)."
                if count else "Nenhuma alteração para salvar."
            )
            st.rerun()
    else:
        st.caption(f"Somente consulta. O preenchimento é realizado por {' e '.join(EDITOR_EMAILS)}.")
        st.dataframe(
            frame[table_columns], column_config=configs, hide_index=True, width="stretch"
        )

    if saved_rows:
        with st.expander("Últimas atualizações"):
            updates = pd.DataFrame([
                {"competencia": MONTHS[month.month], **row}
                for month, rows in month_rows.items()
                for row in rows
                if row["versao"] > 0
            ])
            updates["atualizado_em"] = (
                pd.to_datetime(updates["atualizado_em"], utc=True)
                .dt.tz_convert(ZoneInfo("America/Sao_Paulo"))
                .dt.strftime("%d/%m/%Y %H:%M")
            )
            st.dataframe(updates[[
                "competencia", "regiao", "atualizado_por", "atualizado_em",
            ]].rename(columns={
                "competencia": "Competência",
                "regiao": "Região",
                "atualizado_por": "Atualizado por",
                "atualizado_em": "Atualizado em",
            }), hide_index=True, width="stretch")
    if st.button("Recarregar dados", help="Descarta alterações não salvas e busca os registros atuais."):
        st.session_state.pop("advance_scope", None)
        st.rerun()


def render_advancement(
    repository: Repository,
    identity: Identity,
    authenticator: SupabaseAuthenticator,
):
    """Compõe a página de preenchimento do adiantamento."""
    render_page_header(
        "Adiantamento de meta",
        "Confirme manualmente os atingimentos de cada região e acompanhe os XP gerados.",
    )
    st.caption("1ª semana: 32% · 2ª semana: 56% · 3ª semana: 80% da meta mensal da região.")
    st.caption("Marcado significa atingiu; desmarcado significa não atingiu.")
    if message := st.session_state.pop("advance_saved", None):
        st.success(message)
    render_table(repository, identity, lambda: current_identity(authenticator))


def main():
    """Inicializa identidade visual, autenticação e navegação do painel."""
    page_icon = str(PAGE_ICON_PATH) if PAGE_ICON_PATH.is_file() else "❄️"
    st.set_page_config(page_title="Campanha Polar", page_icon=page_icon, layout="wide")
    apply_polar_style()
    authenticator = configuration()
    if "supabase_auth_session" not in st.session_state:
        render_login(authenticator)
        st.stop()
    # A autenticação delimita todo o restante da aplicação. Nenhum repositório
    # de dados é criado antes de uma sessão válida.
    try:
        identity, data_client = current_identity(authenticator)
    except (PermissionDenied, AuthenticationServiceError):
        st.session_state.pop("supabase_auth_session", None)
        st.warning("Sua sessão expirou ou não pôde ser validada. Entre novamente.")
        render_login(authenticator)
        st.stop()

    if LOGO_PATH.is_file():
        st.logo(str(LOGO_PATH), size="large")
    panel_reference = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    # Erros esperados de negócio são apresentados como aviso; indisponibilidade
    # ou quebra do contrato de dados aparece como erro operacional.
    try:
        panel_updated_at = DataRefreshRepository(data_client).load()
    except DataAccessError:
        panel_updated_at = None
    page = render_sidebar(identity, authenticator, panel_updated_at)
    try:
        repository = Repository(data_client)
        if page == "Visão geral":
            render_overview(
                repository,
                NewCustomersRepository(data_client),
                ReactivatedCustomersRepository(data_client),
                ProductMixRepository(data_client),
                SalesRepository(data_client),
                BudgetRepository(data_client),
                panel_reference,
            )
        elif page == "Análise individual":
            render_individual_analysis(
                repository,
                NewCustomersRepository(data_client),
                ReactivatedCustomersRepository(data_client),
                ProductMixRepository(data_client),
                SalesRepository(data_client),
                panel_reference,
            )
        elif page == "Venda no Quadrimestre":
            render_quadrimester_sales(SalesRepository(data_client), panel_reference)
        elif page == "Clientes novos":
            render_new_customers(NewCustomersRepository(data_client))
        elif page == "Clientes reativados":
            render_reactivated_customers(ReactivatedCustomersRepository(data_client))
        elif page == "Mix de produtos":
            render_product_mix(ProductMixRepository(data_client))
        else:
            render_advancement(repository, identity, authenticator)
    except (PermissionDenied, ConcurrentChange, ValueError) as error:
        st.warning(str(error))
        if st.button("Buscar versão atual"):
            st.session_state.pop("advance_scope", None)
            st.rerun()
    except DataAccessError as error:
        st.error(str(error))


if __name__ == "__main__":
    main()
