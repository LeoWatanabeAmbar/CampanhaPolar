"""Painel Streamlit da campanha Polar."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from polar.adiantamento import (
    EDITOR_EMAILS,
    FIELDS,
    ConcurrentChange,
    Identity,
    PermissionDenied,
    Repository,
)

MONTHS = {9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
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


@st.cache_resource
def get_repository(url: str):
    """Cria a conexão privada e cacheada usada pelo servidor."""
    if not url.startswith(("postgresql://", "postgresql+psycopg2://")):
        raise ValueError("Configure uma conexão PostgreSQL para o painel.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return Repository(create_engine(url, pool_pre_ping=True, connect_args={
        "sslmode": "require", "connect_timeout": 10,
    }, hide_parameters=True))


def configuration():
    """Lê banco e tenant sem expor segredos na interface."""
    try:
        database_url = str(st.secrets["database"]["url"])
        tenant_id = str(st.secrets["access"]["microsoft_tenant_id"])
        provider = st.secrets["auth"]["microsoft"]
        metadata_url = str(provider["server_metadata_url"])
        expected = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration"
        if not tenant_id or metadata_url.lower() != expected.lower():
            raise ValueError("O login Microsoft deve usar o tenant específico da organização.")
        return database_url, tenant_id
    except (KeyError, FileNotFoundError, ValueError):
        render_page_header(
            "Campanha Polar",
            "O painel está pronto para receber a conexão segura com os dados comerciais.",
        )
        st.info("O painel está aguardando a configuração de acesso e banco de dados.")
        st.caption("A configuração está descrita no README do projeto.")
        st.stop()


def current_identity(tenant_id: str):
    """Cria a identidade confiável a partir da sessão Microsoft."""
    return Identity.from_claims(st.user.is_logged_in, st.user.to_dict(), tenant_id)


def render_login():
    """Exibe a entrada corporativa no padrão do Gestão Comercial."""
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
    render_page_header("Campanha Polar", "Entre com sua conta corporativa Microsoft para continuar.")
    if st.button("Entrar com Microsoft", type="primary", width="stretch"):
        st.login("microsoft")
    st.caption("A conta permanece conectada neste navegador por até 30 dias.")


def render_sidebar(identity: Identity):
    """Renderiza navegação, competência e conta conectada."""
    with st.sidebar:
        st.caption("NAVEGAÇÃO")
        page = st.radio(
            "Página",
            ("Visão geral", "Adiantamento de meta"),
            label_visibility="collapsed",
        )
        st.divider()
        month_number = st.selectbox("Competência", list(MONTHS), format_func=MONTHS.get)
        st.divider()
        st.caption("Usuário conectado")
        st.write(identity.email)
        access = "Pode editar o adiantamento" if identity.can_edit else "Acesso para consulta"
        st.caption(access)
        if st.button("Sair", key="polar_logout", width="stretch"):
            st.session_state.clear()
            st.logout()
    return page, date(2026, month_number, 1)


def render_overview(repository: Repository, month: date):
    """Exibe a primeira visão executiva com dados já homologados."""
    render_page_header(
        "Visão geral",
        "Acompanhe metas regionais, fases confirmadas e XP de adiantamento.",
        month,
    )
    rows = repository.load(month)
    goals = repository.goal_rows(month)
    frame = build_overview_frame(rows, goals)
    if frame.empty:
        st.info("Nenhuma região com meta positiva está disponível para esta competência.")
        return

    checked = int(frame["Fases"].sum())
    total_phases = len(frame) * len(FIELDS)
    metric_goal, metric_regions, metric_phases, metric_xp = st.columns(4)
    metric_goal.metric("Meta do mês", format_currency_br(float(frame["Meta"].sum())))
    metric_regions.metric("Regiões participantes", len(frame))
    metric_phases.metric("Fases confirmadas", f"{checked} de {total_phases}")
    metric_xp.metric("XP de adiantamento", f"{checked * 10} XP")

    st.subheader("Cobertura das fases")
    phase_columns = st.columns(3)
    for column, field in zip(phase_columns, FIELDS):
        confirmed = sum(bool(row[field]) for row in rows)
        with column:
            st.caption(LABELS[field])
            st.progress(confirmed / len(rows), text=f"{confirmed} de {len(rows)} regiões")

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


def render_table(repository: Repository, month: date, identity: Identity, recheck_identity):
    """Renderiza a conferência; leitores recebem somente a tabela de consulta."""
    scope = f"{month.isoformat()}:{identity.user_id}"
    if st.session_state.get("advance_scope") != scope:
        st.session_state["advance_rows"] = repository.load(month)
        st.session_state["advance_scope"] = scope
        st.session_state["advance_revision"] = st.session_state.get("advance_revision", 0) + 1
    rows = st.session_state["advance_rows"]
    if not rows:
        st.info("Nenhuma região disponível para esta competência.")
        return
    frame = pd.DataFrame(rows)
    checked = sum(sum(bool(row[field]) for field in FIELDS) for row in rows)
    a, b, c, d = st.columns(4)
    a.metric("Regiões", len(rows))
    b.metric("Atingimentos marcados", checked)
    c.metric("Registros salvos", sum(row["versao"] > 0 for row in rows))
    d.metric("XP de adiantamento", f"{checked * 10} XP")
    configs = {
        "regiao": st.column_config.TextColumn("Região"),
        **{
            field: st.column_config.CheckboxColumn(
                LABELS[field],
                help="Informe manualmente se a região atingiu esta fase. O sistema não calcula nem valida o prazo.",
            )
            for field in FIELDS
        },
        "observacao": st.column_config.TextColumn("Observações", max_chars=2000, width="large"),
    }
    editable_columns = ["regiao", *FIELDS, "observacao"]
    if identity.can_edit:
        st.caption("Marque os atingimentos conferidos. Cada fase é independente.")
        with st.form("advance_form"):
            edited = st.data_editor(
                frame[editable_columns], column_config=configs, disabled=["regiao"],
                num_rows="fixed", hide_index=True, width="stretch",
                key=f"advance_editor:{scope}:{st.session_state['advance_revision']}",
            )
            submitted = st.form_submit_button("Salvar alterações", type="primary", width="stretch")
        if submitted:
            current = recheck_identity()
            if current.user_id != identity.user_id:
                raise PermissionDenied("A conta conectada mudou. Recarregue a página.")
            versions = {row["regiao"]: row["versao"] for row in rows}
            payload = edited.to_dict("records")
            for row in payload:
                row["versao"] = versions.get(row["regiao"], -1)
            count = repository.save(month, payload, current)
            st.session_state.pop("advance_scope", None)
            st.session_state["advance_saved"] = (
                f"Dados salvos: {count} região(ões) atualizada(s)."
                if count else "Nenhuma alteração para salvar."
            )
            st.rerun()
    else:
        st.caption(f"Somente consulta. O preenchimento é realizado por {' e '.join(EDITOR_EMAILS)}.")
        st.dataframe(frame[editable_columns], column_config=configs, hide_index=True, width="stretch")

    saved = frame[frame["versao"] > 0].copy()
    if not saved.empty:
        with st.expander("Últimas atualizações"):
            saved["atualizado_em"] = (
                pd.to_datetime(saved["atualizado_em"], utc=True)
                .dt.tz_convert(ZoneInfo("America/Sao_Paulo"))
                .dt.strftime("%d/%m/%Y %H:%M")
            )
            st.dataframe(saved[["regiao", "atualizado_por", "atualizado_em"]].rename(columns={
                "regiao": "Região",
                "atualizado_por": "Atualizado por",
                "atualizado_em": "Atualizado em",
            }), hide_index=True, width="stretch")
    if st.button("Recarregar dados", help="Descarta alterações não salvas e busca os registros atuais."):
        st.session_state.pop("advance_scope", None)
        st.rerun()


def render_advancement(repository: Repository, month: date, identity: Identity, tenant: str):
    """Compõe a página de preenchimento do adiantamento."""
    render_page_header(
        "Adiantamento de meta",
        "Confirme manualmente os atingimentos de cada região e acompanhe os XP gerados.",
        month,
    )
    st.caption("1ª semana: 32% · 2ª semana: 56% · 3ª semana: 80% da meta mensal da região.")
    st.caption("Marcado significa atingiu; desmarcado significa não atingiu.")
    if message := st.session_state.pop("advance_saved", None):
        st.success(message)
    render_table(repository, month, identity, lambda: current_identity(tenant))


def main():
    """Inicializa identidade visual, autenticação e navegação do painel."""
    page_icon = str(LOGO_PATH) if LOGO_PATH.is_file() else "❄️"
    st.set_page_config(page_title="Campanha Polar", page_icon=page_icon, layout="wide")
    if LOGO_PATH.is_file():
        st.logo(str(LOGO_PATH), size="large")
    apply_polar_style()
    url, tenant = configuration()
    if not st.user.is_logged_in:
        render_login()
        st.stop()
    try:
        identity = current_identity(tenant)
    except PermissionDenied as error:
        st.warning(str(error))
        if st.button("Entrar novamente"):
            st.logout()
        st.stop()

    page, month = render_sidebar(identity)
    try:
        repository = get_repository(url)
        if page == "Visão geral":
            render_overview(repository, month)
        else:
            render_advancement(repository, month, identity, tenant)
    except (PermissionDenied, ConcurrentChange, ValueError) as error:
        st.warning(str(error))
        if st.button("Buscar versão atual"):
            st.session_state.pop("advance_scope", None)
            st.rerun()
    except SQLAlchemyError:
        st.error("Não foi possível acessar os registros. Verifique a conexão e tente novamente.")


if __name__ == "__main__":
    main()
