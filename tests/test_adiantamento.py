from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, func, insert, select
from streamlit.testing.v1 import AppTest

from polar.adiantamento import (
    ConcurrentChange, Identity, PermissionDenied, Repository,
    blank_record, historico, metadata, metas_comerciais, registros,
)

MONTH = date(2026, 9, 1)
EDITOR = Identity("lais.vendrasco@ambar.tech", "user-lais", "tenant-ambar")
LEONARDO = Identity("leonardo.watanabe@ambar.tech", "user-leonardo", "tenant-ambar")
READER = Identity("leitor@ambar.tech", "user-leitor", "tenant-ambar")


@pytest.fixture
def repository(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'adiantamento.db'}", execution_options={
        "schema_translate_map": {"comercial_marts": None},
    })
    metadata.create_all(engine)
    repo = Repository(engine)
    repo.region_names = lambda month: ["REG 01", "REG 02"]
    yield repo
    engine.dispose()


def test_authorization_rejects_reader_before_database_access(repository):
    with pytest.raises(PermissionDenied):
        repository.save(MONTH, [blank_record("REG 01")], READER)
    with repository.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(registros)) == 0


@pytest.mark.parametrize("editor", [EDITOR, LEONARDO])
def test_oidc_requires_login_and_trusted_tenant(editor):
    claims = {"tid": "tenant-ambar", "oid": editor.user_id, "preferred_username": editor.email.upper()}
    assert Identity.from_claims(True, claims, "tenant-ambar").can_edit
    for logged, tenant in [(False, "tenant-ambar"), (True, "other-tenant")]:
        with pytest.raises(PermissionDenied):
            Identity.from_claims(logged, claims, tenant)
    with pytest.raises(PermissionDenied):
        Identity.from_claims(True, dict(claims, exp=(datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()), "tenant-ambar")


@pytest.mark.parametrize("editor", [EDITOR, LEONARDO])
def test_saves_independent_checks_and_persists_after_reconnect(repository, editor):
    row = dict(blank_record("REG 01"), semana_2_56=True, observacao="Conferência manual")
    assert repository.save(MONTH, [row], editor) == 1
    repository.engine.dispose()
    loaded = repository.load(MONTH)[0]
    assert loaded["semana_2_56"] is True
    assert loaded["semana_1_32"] is False
    assert loaded["semana_3_80"] is False
    assert loaded["atualizado_por"] == editor.email
    with repository.engine.connect() as conn:
        event = conn.execute(select(historico)).mappings().one()
    assert event["alterado_por"] == editor.email
    assert event["usuario_id"] == editor.user_id
    assert loaded["versao"] == 1
    assert repository.load(date(2026, 10, 1))[0]["semana_2_56"] is False


def test_uncheck_keeps_history_and_noop_does_not_add_history(repository):
    repository.save(MONTH, [dict(blank_record("REG 01"), semana_1_32=True)], EDITOR)
    loaded = repository.load(MONTH)[0]
    assert repository.save(MONTH, [loaded], EDITOR) == 0
    loaded["semana_1_32"] = False
    assert repository.save(MONTH, [loaded], EDITOR) == 1
    with repository.engine.connect() as conn:
        events = list(conn.execute(select(historico).order_by(historico.c.id)).mappings())
    assert len(events) == 2
    assert events[1]["anterior"]["semana_1_32"] is True
    assert events[1]["novo"]["semana_1_32"] is False
    assert events[1]["usuario_id"] == EDITOR.user_id


def test_conflict_rolls_back_entire_save(repository):
    repository.save(MONTH, [blank_record("REG 02")], EDITOR)
    new_first = dict(blank_record("REG 01"), semana_1_32=True)
    stale_second = blank_record("REG 02")
    with pytest.raises(ConcurrentChange):
        repository.save(MONTH, [new_first, stale_second], EDITOR)
    assert repository.load(MONTH)[0]["versao"] == 0
    with repository.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(historico)) == 1


@pytest.mark.parametrize("change", [
    {"regiao": "REG INVÁLIDA"}, {"semana_1_32": "true"},
    {"versao": -1}, {"observacao": "x" * 2001},
])
def test_invalid_payload_is_rejected(repository, change):
    with pytest.raises(ValueError):
        repository.save(MONTH, [dict(blank_record("REG 01"), **change)], EDITOR)


def test_duplicate_region_and_invalid_month_are_rejected(repository):
    with pytest.raises(ValueError):
        repository.save(MONTH, [blank_record("REG 01"), blank_record("REG 01")], EDITOR)
    with pytest.raises(ValueError):
        repository.save(date(2026, 8, 1), [blank_record("REG 01")], EDITOR)


def test_regions_come_only_from_positive_channel_and_construction_goals(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'metas.db'}", execution_options={
        "schema_translate_map": {"comercial_marts": None},
    })
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(metas_comerciais), [
            {"data": MONTH, "regiao": " REG CANAIS ", "time": "Canais", "meta": 100},
            {"data": MONTH, "regiao": "REG NORTE", "time": "Time Norte", "meta": 200},
            {"data": MONTH, "regiao": "REG SUL", "time": "Time Sul", "meta": 0},
            {"data": MONTH, "regiao": "REG OUTROS", "time": "Outros", "meta": 300},
            {"data": date(2026, 10, 1), "regiao": "REG OUTUBRO", "time": "Canais", "meta": 400},
        ])
    repository = Repository(engine)
    assert repository.region_names(MONTH) == ["REG CANAIS", "REG NORTE"]
    goals = repository.goal_rows(MONTH)
    assert [(row["regiao"], row["time"], float(row["meta"])) for row in goals] == [
        ("REG CANAIS", "Canais", 100.0),
        ("REG NORTE", "Time Norte", 200.0),
    ]
    engine.dispose()


def test_overview_combines_goals_checks_and_regional_xp():
    from app import build_overview_frame

    rows = [
        dict(blank_record("REG 01"), semana_1_32=True, semana_2_56=True),
        blank_record("REG 02"),
    ]
    goals = [
        {"regiao": "REG 01", "time": "Time Norte", "meta": 100_000},
        {"regiao": "REG 02", "time": "Canais", "meta": 50_000},
    ]
    overview = build_overview_frame(rows, goals).set_index("Região")

    assert overview.loc["REG 01", "Meta"] == 100_000
    assert overview.loc["REG 01", "Fases"] == 2
    assert overview.loc["REG 01", "Progresso"] == pytest.approx(2 / 3)
    assert overview.loc["REG 01", "XP"] == 20
    assert overview.loc["REG 02", "XP"] == 0


def ui_runner():
    import streamlit as st
    from datetime import date
    from app import render_table
    render_table(st.session_state["repo"], date(2026, 9, 1), st.session_state["actor"],
                 lambda: st.session_state["current_actor"])


def overview_ui_runner():
    import streamlit as st
    from datetime import date
    from app import render_overview
    render_overview(st.session_state["repo"], date(2026, 9, 1))


def make_ui(repository, actor):
    app = AppTest.from_function(ui_runner)
    app.session_state["repo"] = repository
    app.session_state["actor"] = actor
    app.session_state["current_actor"] = actor
    return app.run(timeout=15)


def test_viewer_ui_has_no_save_button(repository):
    app = make_ui(repository, READER)
    assert not app.exception
    assert not any(button.label == "Salvar alterações" for button in app.button)
    assert len(app.dataframe) == 1


def test_overview_ui_renders_metrics_progress_and_region_table(repository):
    with repository.engine.begin() as connection:
        connection.execute(insert(metas_comerciais), [
            {"data": MONTH, "regiao": "REG 01", "time": "Time Norte", "meta": 100_000},
            {"data": MONTH, "regiao": "REG 02", "time": "Canais", "meta": 50_000},
        ])
    repository.save(MONTH, [
        dict(blank_record("REG 01"), semana_1_32=True),
        blank_record("REG 02"),
    ], EDITOR)
    app = AppTest.from_function(overview_ui_runner)
    app.session_state["repo"] = repository
    app.run(timeout=15)

    assert not app.exception
    assert [metric.label for metric in app.metric] == [
        "Meta do mês", "Regiões participantes", "Fases confirmadas", "XP de adiantamento",
    ]
    assert app.metric[3].value == "10 XP"
    assert len(app.dataframe) == 1


@pytest.mark.parametrize("editor", [EDITOR, LEONARDO])
def test_editor_saves_form_and_reader_can_load_same_records(repository, editor):
    app = make_ui(repository, editor)
    assert not app.exception
    key = f"advance_editor:{MONTH.isoformat()}:{editor.user_id}:1"
    app.session_state[key] = {"edited_rows": {0: {"semana_1_32": True}}, "added_rows": [], "deleted_rows": []}
    next(button for button in app.button if button.label == "Salvar alterações").click().run(timeout=15)
    assert not app.exception
    assert repository.load(MONTH)[0]["semana_1_32"] is True
    viewer = make_ui(repository, READER)
    assert not viewer.exception
    assert bool(viewer.dataframe[0].value.iloc[0]["semana_1_32"])


def test_app_without_configuration_shows_setup_message():
    app = AppTest.from_file("app.py").run(timeout=15)
    assert not app.exception
    assert any("aguardando a configuração" in message.value for message in app.info)
