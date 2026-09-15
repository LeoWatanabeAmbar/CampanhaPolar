"""Acompanhamento regional de vendas contra a meta parcial do mês."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Any, Iterable

from httpx import HTTPError
from postgrest.exceptions import APIError

from polar.adiantamento import (
    DataAccessError,
    PermissionDenied,
    data_api_rejection_message,
    validate_month,
)

LOAD_FUNCTION = "campanha_polar_carregar_vendas_regionais"
SEPTEMBER = date(2026, 9, 1)
NATIONAL_HOLIDAYS_2026 = frozenset({
    date(2026, 9, 7),
    date(2026, 10, 12),
    date(2026, 11, 2),
    date(2026, 11, 15),
    date(2026, 11, 20),
    date(2026, 12, 25),
})


def _decimal(value: object) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError) as error:
        raise DataAccessError("A consulta de vendas devolveu um valor numérico inválido.") from error


def working_days(
    month: date,
    reference: date,
    holidays: Iterable[date] = NATIONAL_HOLIDAYS_2026,
) -> tuple[int, int, int]:
    """Retorna dias úteis totais, decorridos e posteriores à referência."""
    validate_month(month)
    holiday_set = set(holidays)
    last_day = date(month.year, month.month, monthrange(month.year, month.month)[1])
    cursor = month
    valid_days: list[date] = []
    while cursor <= last_day:
        if cursor.weekday() < 5 and cursor not in holiday_set:
            valid_days.append(cursor)
        cursor += timedelta(days=1)
    elapsed = sum(day <= reference for day in valid_days)
    remaining = sum(day > reference for day in valid_days)
    return len(valid_days), elapsed, remaining


def sales_xp(attainment_pct: Decimal | float | int | None) -> int | None:
    """Aplica as faixas confirmadas ao percentual exato, sem arredondá-lo."""
    if attainment_pct is None:
        return None
    percentage = _decimal(attainment_pct)
    if percentage < 60:
        return 0
    if percentage < 70:
        return 100
    if percentage < 80:
        return 200
    if percentage < 90:
        return 350
    if percentage < 100:
        return 450
    if percentage < 110:
        return 500
    if percentage < 120:
        return 550
    if percentage < 130:
        return 600
    completed_blocks = ((percentage - Decimal("130")) / Decimal("10")).to_integral_value(
        rounding=ROUND_FLOOR
    )
    return 650 + 50 * int(completed_blocks)


def calculate_region_results(
    rows: list[dict],
    month: date = SEPTEMBER,
    reference: date | None = None,
) -> list[dict]:
    """Calcula meta parcial, atingimento e XP no grão regional."""
    validate_month(month)
    if reference is None:
        if not rows:
            return []
        try:
            reference = date.fromisoformat(str(rows[0]["data_referencia"]))
        except (KeyError, TypeError, ValueError) as error:
            raise DataAccessError("A consulta de vendas não informou uma data de referência válida.") from error

    total_days, elapsed_days, remaining_days = working_days(month, reference)
    results = []
    for row in rows:
        goal = _decimal(row.get("meta"))
        realized = _decimal(row.get("realizado"))
        daily_goal = goal / total_days if goal > 0 and total_days else None
        partial_goal = daily_goal * elapsed_days if daily_goal is not None and elapsed_days else None
        attainment = (
            realized * Decimal("100") / partial_goal
            if partial_goal is not None and partial_goal > 0
            else None
        )
        balance = max(goal - realized, Decimal("0"))
        required_per_remaining_day = (
            balance / remaining_days if remaining_days else None
        )
        results.append({
            **row,
            "meta": goal,
            "realizado": realized,
            "dias_uteis_mes": total_days,
            "dias_uteis_decorridos": elapsed_days,
            "dias_uteis_restantes": remaining_days,
            "meta_diaria": daily_goal,
            "meta_parcial": partial_goal,
            "atingimento_parcial_pct": attainment,
            "xp": sales_xp(attainment),
            "saldo_meta": balance,
            "necessario_dia_util_restante": required_per_remaining_day,
        })
    return results


class SalesRepository:
    """Carrega meta e realizado regionais pela Data API autenticada."""

    def __init__(self, client: Any):
        self.client = client

    def load(self, month: date = SEPTEMBER) -> list[dict]:
        validate_month(month)
        try:
            data = self.client.rpc(
                LOAD_FUNCTION,
                {"p_competencia": month.isoformat()},
            ).execute().data
        except APIError as error:
            error_text = " ".join((
                str(getattr(error, "code", "") or ""),
                str(getattr(error, "message", "") or ""),
                str(error),
            )).upper()
            if "AUTH_REQUIRED" in error_text or "42501" in error_text:
                raise PermissionDenied("Faça login novamente para consultar as vendas.") from error
            raise DataAccessError(
                data_api_rejection_message(error, "a consulta de Venda no Quadrimestre")
            ) from error
        except HTTPError as error:
            raise DataAccessError("Não foi possível consultar as vendas.") from error

        if data is None:
            return []
        if not isinstance(data, list):
            raise DataAccessError("A consulta de vendas devolveu um formato inesperado.")

        required = {"data_referencia", "regiao", "time", "meta", "realizado", "vendedores"}
        records = []
        for item in data:
            if not isinstance(item, dict):
                raise DataAccessError("A consulta de vendas devolveu um registro inválido.")
            if not required.issubset(item):
                raise DataAccessError(
                    "A função de vendas está desatualizada. Execute novamente "
                    "sql/vendas_quadrimestre.sql no Supabase."
                )
            region = str(item.get("regiao") or "").strip()
            reference = str(item.get("data_referencia") or "").strip()
            if not region or not reference:
                raise DataAccessError("A consulta de vendas devolveu identificação incompleta.")
            records.append({
                "data_referencia": reference,
                "regiao": region,
                "time": str(item.get("time") or "").strip(),
                "meta": _decimal(item.get("meta")),
                "realizado": _decimal(item.get("realizado")),
                "vendedores": str(item.get("vendedores") or "Sem venda elegível").strip(),
            })
        return records
