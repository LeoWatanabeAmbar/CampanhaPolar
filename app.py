"""Painel Streamlit da campanha Polar."""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from polar.autenticacao import AuthenticationServiceError, SupabaseAuthenticator
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
from polar.vendas import SEPTEMBER, SalesRepository, calculate_region_results

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
POLAR_BLUE = "#0072D6"
POLAR_BLUE_DARK = "#005DAD"
POLAR_BLUE_SOFT = "#E8F3FC"
POLAR_INK = "#17233A"
POLAR_BORDER = "#DCE8F4"
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo_polar_horizontal.png"
PAGE_ICON_PATH = Path(__file__).resolve().parent / "assets" / "icone_polar.png"


def apply_polar_style():
    """Replica a identidade visual usada no Gestão Comercial."""
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


def build_overview_frame(rows: list[dict], goals: list[dict]) -> pd.DataFrame:
    """Combina meta e confirmação manual no grão região/competência."""
    goals_by_region = {row["regiao"]: row for row in goals}
    records = []
    for row in rows:
        confirmations = sum(bool(row[field]) for field in FIELDS)
        goal = goals_by_region.get(row["regiao"], {})
        records.append({
            "Região": row["regiao"],
            "Time": goal.get("time", ""),
            "Meta": float(goal.get("meta") or 0),
            LABELS["semana_1_32"]: bool(row["semana_1_32"]),
            LABELS["semana_2_56"]: bool(row["semana_2_56"]),
            LABELS["semana_3_80"]: bool(row["semana_3_80"]),
            "Fases": confirmations,
            "Progresso": confirmations / len(FIELDS),
            "XP": confirmations * 10,
            "Situação": (
                "Todas as fases confirmadas" if confirmations == len(FIELDS)
                else "Em andamento" if confirmations
                else "Sem atingimento marcado"
            ),
        })
    return pd.DataFrame(records)


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
    st.caption("O acesso é restrito aos usuários cadastrados no Supabase Authentication.")


def render_sidebar(identity: Identity, authenticator: SupabaseAuthenticator):
    """Renderiza navegação e conta conectada."""
    with st.sidebar:
        st.caption("NAVEGAÇÃO")
        page = st.radio(
            "Página",
            (
                "Visão geral",
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
        if st.button("Sair", key="polar_logout", width="stretch"):
            saved_session = st.session_state.get("supabase_auth_session", {})
            try:
                authenticator.sign_out(saved_session)
            except AuthenticationServiceError:
                pass
            st.session_state.clear()
            st.rerun()
    return page


def render_overview(repository: Repository):
    """Exibe a visão executiva consolidada das competências com metas publicadas."""
    render_page_header(
        "Visão geral",
        "Acompanhe metas regionais, fases confirmadas e XP de adiantamento na campanha.",
    )
    rows = []
    frames = []
    for month, month_rows in repository.load_campaign().items():
        if not month_rows:
            continue
        rows.extend(month_rows)
        month_frame = build_overview_frame(month_rows, month_rows)
        month_frame.insert(0, "Competência", MONTHS[month.month])
        frames.append(month_frame)
    frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if frame.empty:
        st.info("Nenhuma região com meta positiva está disponível para a campanha.")
        return

    checked = int(frame["Fases"].sum())
    total_phases = len(frame) * len(FIELDS)
    metric_goal, metric_regions, metric_phases, metric_xp = st.columns(4)
    metric_goal.metric("Metas publicadas", format_currency_br(float(frame["Meta"].sum())))
    metric_regions.metric("Regiões participantes", frame["Região"].nunique())
    metric_phases.metric("Fases confirmadas", f"{checked} de {total_phases}")
    metric_xp.metric("XP de adiantamento", f"{checked * 10} XP")

    st.subheader("Cobertura das fases")
    phase_columns = st.columns(3)
    for column, field in zip(phase_columns, FIELDS):
        confirmed = sum(bool(row[field]) for row in rows)
        with column:
            st.caption(LABELS[field])
            st.progress(confirmed / len(rows), text=f"{confirmed} de {len(rows)} região-mês")

    st.subheader("Detalhamento regional")
    st.caption("Cada fase confirmada gera 10 XP para a região.")
    st.dataframe(
        frame,
        column_config={
            "Meta": st.column_config.NumberColumn("Meta", format="R$ %.2f"),
            **{
                LABELS[field]: st.column_config.CheckboxColumn(LABELS[field])
                for field in FIELDS
            },
            "Fases": st.column_config.NumberColumn("Fases", format="%d"),
            "Progresso": st.column_config.ProgressColumn(
                "Progresso", min_value=0.0, max_value=1.0, format="percent",
            ),
            "XP": st.column_config.NumberColumn("XP", format="%d XP"),
        },
        hide_index=True,
        width="stretch",
    )


def render_quadrimester_sales(repository: SalesRepository):
    """Exibe o ritmo de setembro e o XP atual calculado por região."""
    render_page_header(
        "Venda no Quadrimestre",
        "Compare as vendas de setembro com a meta proporcional aos dias úteis decorridos.",
        SEPTEMBER,
    )
    rows = repository.load(SEPTEMBER)
    if not rows:
        st.info("A meta de setembro ainda não está disponível para as regiões participantes.")
        return

    results = calculate_region_results(rows, SEPTEMBER)
    frame = pd.DataFrame(results)
    reference = date.fromisoformat(str(frame.iloc[0]["data_referencia"]))
    elapsed = int(frame.iloc[0]["dias_uteis_decorridos"])
    total_days = int(frame.iloc[0]["dias_uteis_mes"])
    remaining = int(frame.iloc[0]["dias_uteis_restantes"])

    total_goal = sum(frame["meta"])
    total_partial = sum(value for value in frame["meta_parcial"] if value is not None)
    total_realized = sum(frame["realizado"])
    total_attainment = (
        total_realized * 100 / total_partial if total_partial else None
    )

    st.caption(
        f"Referência: {reference:%d/%m/%Y} · {elapsed} de {total_days} dias úteis "
        f"decorridos · {remaining} dias úteis restantes."
    )
    metric_goal, metric_partial, metric_realized, metric_attainment = st.columns(4)
    metric_goal.metric("Meta de setembro", format_currency_br(float(total_goal)))
    metric_partial.metric("Meta parcial até hoje", format_currency_br(float(total_partial)))
    metric_realized.metric("Realizado até hoje", format_currency_br(float(total_realized)))
    metric_attainment.metric(
        "Atingimento da meta parcial",
        format_percentage_br(float(total_attainment)) if total_attainment is not None else "Pendente",
    )

    st.subheader("Venda x meta por região")
    st.caption(
        "O percentual exato, antes da formatação visual, define o XP. O resultado e o XP "
        "permanecem únicos por região; a coluna Vendedores mostra quem compôs suas vendas."
    )
    display = frame.copy()
    display["Dias úteis"] = display.apply(
        lambda row: f"{row['dias_uteis_decorridos']} de {row['dias_uteis_mes']}", axis=1
    )
    display = display.rename(columns={
        "regiao": "Região",
        "vendedores": "Vendedores",
        "realizado": "Realizado",
        "meta_parcial": "Meta parcial",
        "atingimento_parcial_pct": "Atingimento parcial",
        "xp": "XP da região",
        "meta": "Meta mensal",
        "meta_diaria": "Meta diária",
        "saldo_meta": "Saldo da meta",
        "necessario_dia_util_restante": "Necessário/dia restante",
    })
    numeric_columns = [
        "Realizado", "Meta parcial", "Atingimento parcial", "Meta mensal",
        "Meta diária", "Saldo da meta", "Necessário/dia restante",
    ]
    for column in numeric_columns:
        display[column] = display[column].map(
            lambda value: float(value) if value is not None else None
        )
    st.dataframe(
        display[[
            "Região", "Vendedores", "Realizado", "Meta parcial", "Atingimento parcial",
            "XP da região", "Meta mensal", "Meta diária", "Dias úteis", "Saldo da meta",
            "Necessário/dia restante",
        ]],
        column_config={
            "Realizado": st.column_config.NumberColumn("Realizado", format="R$ %.2f"),
            "Meta parcial": st.column_config.NumberColumn("Meta parcial", format="R$ %.2f"),
            "Atingimento parcial": st.column_config.NumberColumn(
                "Atingimento parcial", format="%.1f%%"
            ),
            "XP da região": st.column_config.NumberColumn("XP da região", format="%d XP"),
            "Meta mensal": st.column_config.NumberColumn("Meta mensal", format="R$ %.2f"),
            "Meta diária": st.column_config.NumberColumn("Meta diária", format="R$ %.2f"),
            "Saldo da meta": st.column_config.NumberColumn("Saldo da meta", format="R$ %.2f"),
            "Necessário/dia restante": st.column_config.NumberColumn(
                "Necessário/dia restante", format="R$ %.2f"
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
    if LOGO_PATH.is_file():
        st.logo(str(LOGO_PATH), size="large")
    apply_polar_style()
    authenticator = configuration()
    if "supabase_auth_session" not in st.session_state:
        render_login(authenticator)
        st.stop()
    try:
        identity, data_client = current_identity(authenticator)
    except (PermissionDenied, AuthenticationServiceError):
        st.session_state.pop("supabase_auth_session", None)
        st.warning("Sua sessão expirou ou não pôde ser validada. Entre novamente.")
        render_login(authenticator)
        st.stop()

    page = render_sidebar(identity, authenticator)
    try:
        repository = Repository(data_client)
        if page == "Visão geral":
            render_overview(repository)
        elif page == "Venda no Quadrimestre":
            render_quadrimester_sales(SalesRepository(data_client))
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
