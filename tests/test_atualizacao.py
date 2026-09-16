from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from polar.atualizacao import DataRefreshRepository, REFRESH_KEYS, parse_refresh_datetime


class FakeRequest:
    def __init__(self, data):
        self.data = data
        self.operations = []

    def select(self, columns):
        self.operations.append(("select", columns))
        return self

    def in_(self, column, values):
        self.operations.append(("in", column, values))
        return self

    def order(self, column, desc=False):
        self.operations.append(("order", column, desc))
        return self

    def limit(self, value):
        self.operations.append(("limit", value))
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeClient:
    def __init__(self, data):
        self.request = FakeRequest(data)
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return self.request


def test_repository_loads_latest_dataflow_refresh_in_sao_paulo_timezone():
    client = FakeClient([
        {
            "chave": "dataflow_cpv_public",
            "status": "CONCLUIDO",
            "finalizado_em": "2026-09-16T18:42:15+00:00",
            "atualizado_em": "2026-09-16T18:42:15+00:00",
        }
    ])

    result = DataRefreshRepository(client).load()

    assert client.table_name == "cpv_refresh_controle"
    assert ("in", "chave", list(REFRESH_KEYS)) in client.request.operations
    assert ("order", "atualizado_em", True) in client.request.operations
    assert result == datetime(2026, 9, 16, 15, 42, 15, tzinfo=ZoneInfo("America/Sao_Paulo"))


def test_repository_falls_back_to_updated_at_and_does_not_use_current_time():
    client = FakeClient([
        {
            "chave": "totvs_supabase",
            "finalizado_em": None,
            "atualizado_em": "2026-09-16T10:05:00Z",
        }
    ])

    result = DataRefreshRepository(client).load()

    assert result == datetime(2026, 9, 16, 7, 5, tzinfo=ZoneInfo("America/Sao_Paulo"))


def test_repository_returns_none_without_refresh_record():
    assert DataRefreshRepository(FakeClient([])).load() is None


def test_invalid_refresh_datetime_returns_none():
    assert parse_refresh_datetime("invalid") is None
