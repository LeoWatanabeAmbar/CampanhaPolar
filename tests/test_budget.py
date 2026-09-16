from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from polar.budget import ANNUAL_BUDGET, LOAD_FUNCTION, BudgetRepository


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


def test_repository_loads_annual_budget_attainment():
    client = FakeClient([{"data_referencia": "2026-09-16", "realizado": "59500000"}])
    result = BudgetRepository(client).load()

    assert client.calls == [(LOAD_FUNCTION, {})]
    assert result["budget"] == ANNUAL_BUDGET
    assert result["realizado"] == Decimal("59500000")
    assert result["atingimento_pct"] == Decimal("50")


def test_sql_applies_confirmed_annual_sales_rules():
    sql = Path("sql/budget_anual.sql").read_text(encoding="utf-8").lower()

    assert "security definer" in sql
    assert "set search_path = ''" in sql
    assert "set statement_timeout = '60s'" in sql
    assert "at time zone 'america/sao_paulo'" in sql
    assert "date '2026-01-01'" in sql
    assert "f.is_item_valido_metricas is true" in sql
    assert "f.is_venda_comercial is true" in sql
    assert "vw_clientes_inadimplentes" not in sql
    assert "vendas_bloqueadas_faturadas" not in sql
    assert "sum(coalesce(f.valor_bruto_total, 0))" in sql
    assert "fct_faturamento_item" not in sql
    assert "fct_nota_devolucao" in sql
    assert "sum(d.valor_devolucao_alocado)" in sql
    assert "d.data_devolucao >= date '2026-01-01'" in sql
    assert "d.data_devolucao <= v_hoje" in sql
    assert "nota_fiscal_original_id" not in sql
    assert "(v.valor_bruto - d.valor_devolvido)::numeric" in sql
    assert "grant execute on function public.campanha_polar_carregar_budget_anual()" in sql


def test_budget_migration_removes_delinquency_filter():
    sql = Path(
        "sql/migrations/20260916_budget_sem_inadimplencia.sql"
    ).read_text(encoding="utf-8").lower()

    assert "create or replace function public.campanha_polar_carregar_budget_anual()" in sql
    assert "vw_clientes_inadimplentes" not in sql
    assert "vendas_bloqueadas_faturadas" not in sql
    assert "sum(coalesce(f.valor_bruto_total, 0))" in sql


def test_budget_migration_subtracts_every_return_from_2026():
    sql = Path(
        "sql/migrations/20260916_budget_todas_devolucoes_2026.sql"
    ).read_text(encoding="utf-8-sig").lower()

    assert "create or replace function public.campanha_polar_carregar_budget_anual()" in sql
    assert "sum(d.valor_devolucao_alocado)" in sql
    assert "d.data_devolucao >= date '2026-01-01'" in sql
    assert "d.data_devolucao <= v_hoje" in sql
    assert "nota_fiscal_original_id" not in sql
    assert "fct_faturamento_item" not in sql
    assert "(v.valor_bruto - d.valor_devolvido)::numeric" in sql
