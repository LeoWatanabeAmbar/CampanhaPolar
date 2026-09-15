from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from postgrest.exceptions import APIError
from streamlit.testing.v1 import AppTest

from polar.adiantamento import (
    LOAD_FUNCTION,
    SAVE_FUNCTION,
    ConcurrentChange,
    Identity,
    PermissionDenied,
    Repository,
    blank_record,
)

MONTH = date(2026, 9, 1)
EDITOR = Identity("lais.vendrasco@ambar.tech", "user-lais")
LEONARDO = Identity("leonardo.watanabe@ambar.tech", "user-leonardo")
READER = Identity("leitor@ambar.tech", "user-leitor")


class FakeRequest:
    def __init__(self, client, function, parameters):
        self.client = client
        self.function = function
        self.parameters = parameters

    def execute(self):
        return SimpleNamespace(data=self.client.execute(self.function, self.parameters))


class FakeDataApi:
    """Simula somente o contrato das duas funções SQL usadas pelo painel."""

    def __init__(self):
        self.goals = {
            MONTH.isoformat(): [
                {"regiao": "REG 01", "time": "Time Norte", "meta": 100_000},
                {"regiao": "REG 02", "time": "Canais", "meta": 50_000},
            ],
        }
        self.state = {}
        self.history = []
        self.calls = []

    def rpc(self, function, parameters):
        self.calls.append((function, deepcopy(parameters)))
        return FakeRequest(self, function, parameters)

    def execute(self, function, parameters):
        if function == LOAD_FUNCTION:
            return self._load(parameters["p_competencia"])
        if function == SAVE_FUNCTION:
            return self._save(parameters["p_competencia"], parameters["p_registros"])
        raise AssertionError(f"RPC inesperada: {function}")

    def _load(self, month):
        result = []
        for goal in self.goals.get(month, []):
            saved = self.state.get((month, goal["regiao"]), {})
            result.append({**blank_record(goal["regiao"]), **goal, **saved})
        return result

    def _save(self, month, rows):
        allowed = {goal["regiao"] for goal in self.goals.get(month, [])}
        staged_state = deepcopy(self.state)
        staged_history = deepcopy(self.history)
        changed = 0
        for row in rows:
            region = row["regiao"]
            if region not in allowed:
                raise APIError({"code": "22023", "message": "INVALID_REGION"})
            key = (month, region)
            old = staged_state.get(key)
            old_version = old["versao"] if old else 0
            if row["versao"] != old_version:
                raise APIError({"code": "40001", "message": "CONCURRENT_CHANGE"})
            values = {
                field: row[field]
                for field in ("semana_1_32", "semana_2_56", "semana_3_80", "observacao")
            }
            previous = {field: old[field] for field in values} if old else None
            if previous == values:
                continue
            now = datetime.now(timezone.utc).isoformat()
            saved = {
                **values,
                "versao": old_version + 1,
                "atualizado_em": now,
                "atualizado_por": EDITOR.email,
            }
            staged_state[key] = saved
            staged_history.append({
                "competencia": month,
                "regiao": region,
                "versao": old_version + 1,
                "anterior": previous,
                "novo": values,
            })
            changed += 1
        self.state = staged_state
        self.history = staged_history
        return changed


@pytest.fixture
def api():
    return FakeDataApi()


@pytest.fixture
def repository(api):
    return Repository(api)


def test_authorization_rejects_reader_before_data_api_access(repository, api):
    with pytest.raises(PermissionDenied):
        repository.save(MONTH, [blank_record("REG 01")], READER)
    assert api.calls == []


@pytest.mark.parametrize("editor", [EDITOR, LEONARDO])
def test_identity_uses_validated_supabase_user(editor):
    identity = Identity.from_authenticated_user({
        "id": editor.user_id,
        "email": editor.email.upper(),
    })
    assert identity.can_edit
    assert identity.email == editor.email
    with pytest.raises(PermissionDenied):
        Identity.from_authenticated_user({"id": "", "email": editor.email})


@pytest.mark.parametrize("editor", [EDITOR, LEONARDO])
def test_saves_independent_checks_and_loads_through_rpc(repository, api, editor):
    row = dict(blank_record("REG 01"), semana_2_56=True, observacao="Conferência manual")
    assert repository.save(MONTH, [row], editor) == 1
    loaded = repository.load(MONTH)[0]
    assert loaded["semana_2_56"] is True
    assert loaded["semana_1_32"] is False
    assert loaded["semana_3_80"] is False
    assert loaded["versao"] == 1
    assert len(api.history) == 1
    assert repository.load(date(2026, 10, 1)) == []
    assert api.calls[0][0] == SAVE_FUNCTION
    assert api.calls[1][0] == LOAD_FUNCTION


def test_uncheck_keeps_history_and_noop_does_not_add_history(repository, api):
    repository.save(MONTH, [dict(blank_record("REG 01"), semana_1_32=True)], EDITOR)
    loaded = repository.load(MONTH)[0]
    assert repository.save(MONTH, [loaded], EDITOR) == 0
    loaded["semana_1_32"] = False
    assert repository.save(MONTH, [loaded], EDITOR) == 1
    assert len(api.history) == 2
    assert api.history[1]["anterior"]["semana_1_32"] is True
    assert api.history[1]["novo"]["semana_1_32"] is False


def test_conflict_rolls_back_entire_rpc(repository, api):
    repository.save(MONTH, [blank_record("REG 02")], EDITOR)
    new_first = dict(blank_record("REG 01"), semana_1_32=True)
    stale_second = blank_record("REG 02")
    with pytest.raises(ConcurrentChange):
        repository.save(MONTH, [new_first, stale_second], EDITOR)
    assert repository.load(MONTH)[0]["versao"] == 0
    assert len(api.history) == 1


@pytest.mark.parametrize("change", [
    {"regiao": " REG 01"},
    {"semana_1_32": "true"},
    {"versao": -1},
    {"observacao": "x" * 2001},
])
def test_invalid_payload_is_rejected_before_rpc(repository, api, change):
    with pytest.raises(ValueError):
        repository.save(MONTH, [dict(blank_record("REG 01"), **change)], EDITOR)
    assert api.calls == []


def test_duplicate_region_and_invalid_month_are_rejected(repository):
    with pytest.raises(ValueError):
        repository.save(MONTH, [blank_record("REG 01"), blank_record("REG 01")], EDITOR)
    with pytest.raises(ValueError):
        repository.save(date(2026, 8, 1), [blank_record("REG 01")], EDITOR)


def test_region_without_goal_is_rejected_by_server(repository):
    with pytest.raises(ValueError):
        repository.save(MONTH, [blank_record("REG INVÁLIDA")], EDITOR)


def test_sql_secures_rpc_and_filters_goal_regions():
    sql = Path("sql/adiantamento_meta.sql").read_text(encoding="utf-8").lower()
    assert sql.count("security definer") == 2
    assert sql.count("set search_path = ''") == 2
    assert "grant execute on function public.campanha_polar_carregar_adiantamento(date) to authenticated" in sql
    assert "grant execute on function public.campanha_polar_salvar_adiantamento(date, jsonb) to authenticated" in sql
    assert "from public, anon" in sql
    assert "upper(trim(m.time)) in ('canais', 'time norte', 'time sul')" in sql
    assert "(select auth.jwt()) ->> 'email'" in sql


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
    render_table(
        st.session_state["repo"],
        date(2026, 9, 1),
        st.session_state["actor"],
        lambda: (st.session_state["current_actor"], None),
    )


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
    app.session_state[key] = {
        "edited_rows": {0: {"semana_1_32": True}},
        "added_rows": [],
        "deleted_rows": [],
    }
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
