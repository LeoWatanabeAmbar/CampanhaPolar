"""Painel Streamlit da campanha Polar."""
from __future__ import annotations

from datetime import date
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
    region_names = sorted({
        region.strip()
        for value in frame["regioes"]
        for region in str(value).split(" · ")
        if region.strip()
    })
    filter_region, filter_status, filter_search = st.columns((1, 1, 2))
    with filter_region:
        selected_region = st.selectbox("Região", ["Todas", *region_names])
    with filter_status:
        selected_status = st.selectbox("Atribuição", ["Todas", "Confirmadas", "Pendentes"])
    with filter_search:
        search = st.text_input("Buscar", placeholder="Grupo, pedido ou vendedor")

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regioes"].map(
            lambda value: selected_region in {item.strip() for item in str(value).split(" · ")}
        )]
    pending = filtered["situacao_atribuicao"].str.startswith("Pendente")
    if selected_status == "Confirmadas":
        filtered = filtered[~pending]
    elif selected_status == "Pendentes":
        filtered = filtered[pending]
    if normalized_search := search.strip():
        searchable = filtered[[
            "grupo_comercial_id", "nome_grupo_comercial", "pedidos", "vendedores", "regioes",
        ]].astype(str).agg(" ".join, axis=1)
        filtered = filtered[searchable.str.contains(normalized_search, case=False, regex=False)]

    a, b, c, d = st.columns(4)
    a.metric("Clientes novos", len(filtered))
    b.metric("Pedidos no primeiro evento", int(filtered["quantidade_pedidos"].sum()))
    c.metric("Valor líquido elegível", format_currency_br(float(filtered["valor_liquido_elegivel"].sum())))
    d.metric("XP bruto confirmado", f"{float(filtered['xp_evento'].sum()):g} XP")

    pending_count = int(filtered["situacao_atribuicao"].str.startswith("Pendente").sum())
    if pending_count:
        st.warning(
            f"{pending_count} cliente(s) novo(s) possuem atribuição pendente e ainda não geram XP."
        )

    st.subheader("Primeiros eventos de compra")
    st.caption(
        "Pedidos do mesmo grupo na mesma data formam um evento. O XP exibido é anterior ao teto "
        "individual de 100 XP para clientes novos."
    )
    display = filtered.copy()
    first_purchase = pd.to_datetime(display["data_primeira_compra"], errors="coerce")
    display["competencia"] = first_purchase.dt.month.map(MONTHS)
    display["data_primeira_compra"] = first_purchase.dt.strftime("%d/%m/%Y")
    display = display.rename(columns={
        "competencia": "Competência",
        "grupo_comercial_id": "Código",
        "nome_grupo_comercial": "Grupo comercial",
        "data_primeira_compra": "Primeira compra",
        "pedidos": "Pedidos",
        "quantidade_pedidos": "Qtd. pedidos",
        "vendedores": "Vendedores",
        "regioes": "Regiões",
        "segmento": "Segmento",
        "valor_liquido_elegivel": "Valor elegível",
        "situacao_atribuicao": "Atribuição",
        "xp_evento": "XP do evento",
        "xp_por_vendedor": "XP por vendedor",
    })
    st.dataframe(
        display[[
            "Competência", "Primeira compra", "Código", "Grupo comercial", "Pedidos", "Qtd. pedidos",
            "Vendedores", "Regiões", "Segmento", "Valor elegível", "Atribuição",
            "XP do evento", "XP por vendedor",
        ]],
        column_config={
            "Valor elegível": st.column_config.NumberColumn("Valor elegível", format="R$ %.2f"),
            "XP do evento": st.column_config.NumberColumn("XP do evento", format="%.0f XP"),
            "XP por vendedor": st.column_config.NumberColumn("XP por vendedor", format="%.0f XP"),
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
    region_names = sorted({
        region.strip()
        for value in frame["regioes"]
        for region in str(value).split(" · ")
        if region.strip()
    })
    filter_region, filter_status, filter_search = st.columns((1, 1, 2))
    with filter_region:
        selected_region = st.selectbox("Região", ["Todas", *region_names], key="reactivated_region")
    with filter_status:
        selected_status = st.selectbox(
            "Atribuição", ["Todas", "Confirmadas", "Pendentes"], key="reactivated_status"
        )
    with filter_search:
        search = st.text_input(
            "Buscar", placeholder="Grupo, pedido ou vendedor", key="reactivated_search"
        )

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regioes"].map(
            lambda value: selected_region in {item.strip() for item in str(value).split(" · ")}
        )]
    pending = filtered["situacao_atribuicao"].str.startswith("Pendente")
    if selected_status == "Confirmadas":
        filtered = filtered[~pending]
    elif selected_status == "Pendentes":
        filtered = filtered[pending]
    if normalized_search := search.strip():
        searchable = filtered[[
            "grupo_comercial_id", "nome_grupo_comercial", "pedidos", "vendedores", "regioes",
        ]].astype(str).agg(" ".join, axis=1)
        filtered = filtered[searchable.str.contains(normalized_search, case=False, regex=False)]

    a, b, c, d = st.columns(4)
    a.metric("Clientes reativados", len(filtered))
    b.metric("Pedidos no retorno", int(filtered["quantidade_pedidos"].sum()))
    c.metric(
        "Valor líquido elegível",
        format_currency_br(float(filtered["valor_liquido_elegivel"].sum())),
    )
    d.metric("XP bruto confirmado", f"{float(filtered['xp_evento'].sum()):g} XP")

    pending_count = int(filtered["situacao_atribuicao"].str.startswith("Pendente").sum())
    if pending_count:
        st.warning(
            f"{pending_count} cliente(s) reativado(s) possuem atribuição pendente e ainda não geram XP."
        )

    st.subheader("Eventos de reativação")
    st.caption(
        "Canais exige 6 meses e Construção exige 12 meses sem compra. O XP exibido é anterior "
        "ao teto individual acumulado de 80 XP."
    )
    display = filtered.copy()
    activation = pd.to_datetime(display["data_reativacao"], errors="coerce")
    display["competencia"] = activation.dt.month.map(MONTHS)
    display["data_reativacao"] = activation.dt.strftime("%d/%m/%Y")
    display["data_ultima_compra"] = pd.to_datetime(
        display["data_ultima_compra"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    display["prazo_meses"] = display["prazo_meses"].map(lambda value: f"{value} meses")
    display = display.rename(columns={
        "competencia": "Competência",
        "grupo_comercial_id": "Código",
        "nome_grupo_comercial": "Grupo comercial",
        "data_reativacao": "Reativação",
        "data_ultima_compra": "Última compra",
        "prazo_meses": "Prazo",
        "pedidos": "Pedidos",
        "quantidade_pedidos": "Qtd. pedidos",
        "vendedores": "Vendedores",
        "regioes": "Regiões",
        "segmento": "Segmento",
        "valor_liquido_elegivel": "Valor elegível",
        "situacao_atribuicao": "Atribuição",
        "xp_evento": "XP do evento",
        "xp_por_vendedor": "XP por vendedor",
    })
    st.dataframe(
        display[[
            "Competência", "Reativação", "Última compra", "Prazo", "Código",
            "Grupo comercial", "Pedidos", "Qtd. pedidos", "Vendedores", "Regiões",
            "Segmento", "Valor elegível", "Atribuição", "XP do evento", "XP por vendedor",
        ]],
        column_config={
            "Valor elegível": st.column_config.NumberColumn("Valor elegível", format="R$ %.2f"),
            "XP do evento": st.column_config.NumberColumn("XP do evento", format="%.0f XP"),
            "XP por vendedor": st.column_config.NumberColumn("XP por vendedor", format="%.0f XP"),
        },
        hide_index=True,
        width="stretch",
    )


def render_product_mix(repository: ProductMixRepository):
    """Exibe as primeiras compras das famílias de expansão de mix."""
    render_page_header(
        "Mix de produtos",
        "Acompanhe a primeira compra de cada família, seus mínimos e os XP atribuídos.",
    )
    rows = repository.load()
    if not rows:
        st.info("Nenhum evento de expansão de mix foi identificado na campanha.")
        return

    frame = pd.DataFrame(rows)
    region_names = sorted({
        region.strip()
        for value in frame["regioes"]
        for region in str(value).split(" · ")
        if region.strip()
    })
    product_groups = sorted(frame["grupo_mix"].dropna().unique())
    filter_region, filter_product, filter_status, filter_search = st.columns((1, 1, 1, 2))
    with filter_region:
        selected_region = st.selectbox("Região", ["Todas", *region_names], key="mix_region")
    with filter_product:
        selected_product = st.selectbox(
            "Família", ["Todas", *product_groups], key="mix_product"
        )
    with filter_status:
        selected_status = st.selectbox(
            "Resultado", ["Todos", "Com XP", "Pendentes", "Sem XP"], key="mix_status"
        )
    with filter_search:
        search = st.text_input(
            "Buscar", placeholder="Grupo, produto, pedido ou vendedor", key="mix_search"
        )

    filtered = frame.copy()
    if selected_region != "Todas":
        filtered = filtered[filtered["regioes"].map(
            lambda value: selected_region in {item.strip() for item in str(value).split(" · ")}
        )]
    if selected_product != "Todas":
        filtered = filtered[filtered["grupo_mix"] == selected_product]
    pending = filtered["situacao_evento"].str.startswith("Pendente")
    if selected_status == "Com XP":
        filtered = filtered[filtered["xp_evento"] > 0]
    elif selected_status == "Pendentes":
        filtered = filtered[pending]
    elif selected_status == "Sem XP":
        filtered = filtered[(filtered["xp_evento"] <= 0) & ~pending]
    if normalized_search := search.strip():
        searchable = filtered[[
            "grupo_comercial_id", "nome_grupo_comercial", "grupo_mix", "produtos",
            "pedidos", "vendedores", "regioes",
        ]].astype(str).agg(" ".join, axis=1)
        filtered = filtered[searchable.str.contains(normalized_search, case=False, regex=False)]

    a, b, c, d = st.columns(4)
    a.metric("Linhas avaliadas", len(filtered))
    b.metric("Expansões confirmadas", int((filtered["xp_evento"] > 0).sum()))
    c.metric(
        "Valor das linhas",
        format_currency_br(float(filtered["valor_linha_elegivel"].sum())),
    )
    d.metric("XP confirmado", f"{float(filtered['xp_evento'].sum()):g} XP")

    pending_count = int(filtered["situacao_evento"].str.startswith("Pendente").sum())
    if pending_count:
        st.warning(
            f"{pending_count} evento(s) de mix possuem dados pendentes e ainda não geram XP."
        )

    st.subheader("Primeiras compras por família")
    st.caption(
        "Cada grupo comercial pode gerar 10 XP uma vez por família. Clientes KA não pontuam. "
        "O indicador não possui teto individual."
    )
    display = filtered.copy()
    event_date = pd.to_datetime(display["data_expansao"], errors="coerce")
    display["competencia"] = event_date.dt.month.map(MONTHS)
    display["data_expansao"] = event_date.dt.strftime("%d/%m/%Y")
    display = display.rename(columns={
        "competencia": "Competência",
        "data_expansao": "Primeira compra",
        "grupo_comercial_id": "Código",
        "nome_grupo_comercial": "Grupo comercial",
        "grupo_mix": "Família",
        "produtos": "Produtos",
        "pedidos": "Pedidos",
        "quantidade_pedidos": "Qtd. pedidos",
        "vendedores": "Vendedores",
        "regioes": "Regiões",
        "segmento": "Segmento",
        "valor_linha_elegivel": "Valor da linha",
        "valor_minimo": "Mínimo",
        "situacao_evento": "Resultado",
        "xp_evento": "XP do evento",
        "xp_por_vendedor": "XP por vendedor",
    })
    st.dataframe(
        display[[
            "Competência", "Primeira compra", "Código", "Grupo comercial", "Família",
            "Produtos", "Pedidos", "Qtd. pedidos", "Vendedores", "Regiões", "Segmento",
            "Valor da linha", "Mínimo", "Resultado", "XP do evento", "XP por vendedor",
        ]],
        column_config={
            "Valor da linha": st.column_config.NumberColumn("Valor da linha", format="R$ %.2f"),
            "Mínimo": st.column_config.NumberColumn("Mínimo", format="R$ %.2f"),
            "XP do evento": st.column_config.NumberColumn("XP do evento", format="%.0f XP"),
            "XP por vendedor": st.column_config.NumberColumn("XP por vendedor", format="%.0f XP"),
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
    except DataAccessError:
        st.error("Não foi possível acessar os registros pela Data API do Supabase. Tente novamente.")


if __name__ == "__main__":
    main()
