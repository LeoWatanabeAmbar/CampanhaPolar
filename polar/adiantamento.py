"""Domínio e persistência dos checks manuais de adiantamento.

O módulo aplica validações rápidas no cliente, mas a autorização definitiva,
a concorrência otimista e o histórico são responsabilidade das funções SQL.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from httpx import HTTPError
from postgrest.exceptions import APIError

# A allowlist é repetida no banco por defesa em profundidade. Alterações nesta
# tupla exigem migration das constraints/funções e atualização dos testes.
EDITOR_EMAILS = (
    "lais.vendrasco@ambar.tech",
    "leonardo.watanabe@ambar.tech",
    "jorge.castro@ambar.tech",
    "anyelle.santos@ambar.tech",
    "luis.oliveira@ambar.tech",
)
# Os três booleanos são decisões independentes; uma fase posterior não implica
# que as anteriores tenham sido confirmadas.
FIELDS = ("semana_1_32", "semana_2_56", "semana_3_80")
LOAD_FUNCTION = "campanha_polar_carregar_adiantamento"
SAVE_FUNCTION = "campanha_polar_salvar_adiantamento"
SAVE_CAMPAIGN_FUNCTION = "campanha_polar_salvar_adiantamento_campanha"
CAMPAIGN_MONTHS = tuple(date(2026, month, 1) for month in (9, 10, 11, 12))


class PermissionDenied(ValueError):
    pass


class ConcurrentChange(ValueError):
    pass


class DataAccessError(RuntimeError):
    pass


@dataclass(frozen=True)
class Identity:
    """Identidade recebida de uma sessão validada pelo Supabase Auth."""

    email: str
    user_id: str
    auth_source: str = "supabase"

    @classmethod
    def from_authenticated_user(cls, user: dict[str, str]):
        email = str(user.get("email") or "").strip().lower()
        user_id = str(user.get("id") or "").strip()
        if not email or not user_id:
            raise PermissionDenied("Não foi possível identificar a conta conectada.")
        return cls(email=email, user_id=user_id)

    @property
    def can_edit(self):
        # A checagem local controla a experiência da UI. A função SQL repete a
        # decisão usando o e-mail e o ID extraídos diretamente do JWT.
        return bool(self.user_id and self.email in EDITOR_EMAILS)


def validate_month(month: date):
    # A competência é sempre representada pelo primeiro dia para que Python,
    # JSON e PostgreSQL compartilhem a mesma chave canônica.
    if (
        not isinstance(month, date)
        or month.day != 1
        or month.year != 2026
        or month.month not in (9, 10, 11, 12)
    ):
        raise ValueError("Escolha uma competência de setembro a dezembro de 2026.")


def blank_record(region: str):
    # Versão zero identifica uma linha virtual, derivada da meta, que ainda não
    # existe na tabela persistida.
    return {
        "regiao": region,
        "time": "",
        "meta": 0,
        **{field: False for field in FIELDS},
        "observacao": "",
        "versao": 0,
        "atualizado_em": None,
        "atualizado_por": "",
    }


def _api_error_text(error: APIError) -> str:
    details = getattr(error, "details", "") or ""
    message = getattr(error, "message", "") or ""
    code = getattr(error, "code", "") or ""
    return " ".join((str(code), str(message), str(details), str(error))).upper()


def data_api_rejection_message(error: APIError, operation: str) -> str:
    """Expõe o código e a mensagem do PostgREST sem incluir detalhes da consulta."""
    # O detalhe técnico da consulta não é exposto. Código e mensagem do
    # PostgREST são suficientes para diagnóstico sem vazar SQL ou parâmetros.
    code = str(getattr(error, "code", "") or "").strip()
    message = " ".join(str(getattr(error, "message", "") or "").split())
    prefix = f"A Data API recusou {operation}."
    if code and message:
        return f"{prefix} Código {code}: {message}"
    if code:
        return f"{prefix} Código {code}."
    if message:
        return f"{prefix} Detalhe: {message}"
    return prefix


class Repository:
    """Chama funções SQL restritas usando o JWT do usuário autenticado."""

    def __init__(self, client: Any):
        self.client = client

    def _rpc(self, function: str, parameters: dict[str, Any]):
        try:
            return self.client.rpc(function, parameters).execute().data
        except APIError as error:
            text = _api_error_text(error)
            # Erros estáveis emitidos pelo SQL são traduzidos para exceções de
            # domínio, mantendo a UI independente de códigos do PostgreSQL.
            if "CONCURRENT_CHANGE" in text:
                raise ConcurrentChange(
                    "Os registros mudaram em outra sessão. Recarregue antes de salvar."
                ) from error
            if "PERMISSION_DENIED" in text or "AUTH_REQUIRED" in text or "42501" in text:
                raise PermissionDenied("Sua conta não possui permissão para esta operação.") from error
            if "INVALID_" in text:
                raise ValueError("Os dados enviados são inválidos. Recarregue e tente novamente.") from error
            raise DataAccessError("A Data API do Supabase recusou a operação.") from error
        except HTTPError as error:
            raise DataAccessError("Não foi possível acessar a Data API do Supabase.") from error

    def load(self, month: date):
        """Carrega meta e confirmação no grão região/competência."""
        validate_month(month)
        data = self._rpc(LOAD_FUNCTION, {"p_competencia": month.isoformat()})
        if data is None:
            return []
        if not isinstance(data, list):
            raise DataAccessError("A Data API devolveu um formato inesperado.")

        records = []
        for item in data:
            if not isinstance(item, dict) or not str(item.get("regiao") or "").strip():
                raise DataAccessError("A Data API devolveu uma região inválida.")
            # O registro em branco fornece defaults seguros para regiões que
            # ganharam meta, mas ainda não têm uma linha de adiantamento salva.
            row = blank_record(str(item["regiao"]).strip())
            row.update({
                "time": str(item.get("time") or ""),
                "meta": float(item.get("meta") or 0),
                **{field: bool(item.get(field, False)) for field in FIELDS},
                "observacao": str(item.get("observacao") or ""),
                "versao": int(item.get("versao") or 0),
                "atualizado_em": item.get("atualizado_em"),
                "atualizado_por": str(item.get("atualizado_por") or ""),
            })
            records.append(row)
        return records

    def load_campaign(self) -> dict[date, list[dict]]:
        """Carrega as quatro competências para as visões consolidadas."""
        return {month: self.load(month) for month in CAMPAIGN_MONTHS}

    @staticmethod
    def _validate_rows(rows: list[dict]) -> list[dict]:
        seen: set[str] = set()
        payload = []
        # Validamos o lote inteiro antes de chamar a rede. O banco repetirá as
        # mesmas garantias porque clientes externos também podem invocar a RPC.
        for row in rows:
            region = row.get("regiao")
            if not isinstance(region, str) or not region.strip() or region != region.strip() or region in seen:
                raise ValueError("A lista de regiões foi alterada. Recarregue os dados.")
            seen.add(region)
            if any(type(row.get(field)) is not bool for field in FIELDS):
                raise ValueError("Preencha os atingimentos com os checks da tabela.")
            if type(row.get("versao")) is not int or row["versao"] < 0:
                raise ValueError("Versão inválida. Recarregue os dados.")
            if not isinstance(row.get("observacao"), str) or len(row["observacao"]) > 2000:
                raise ValueError("A observação deve ter até 2.000 caracteres.")
            payload.append({
                "regiao": region,
                **{field: row[field] for field in FIELDS},
                "observacao": row["observacao"],
                "versao": row["versao"],
            })
        return payload

    def save(self, month: date, rows: list[dict], identity: Identity):
        """Valida o formato localmente; o banco valida novamente identidade e dados."""
        if not identity.can_edit:
            raise PermissionDenied(f"Somente {' e '.join(EDITOR_EMAILS)} podem salvar alterações.")
        validate_month(month)
        payload = self._validate_rows(rows)

        data = self._rpc(SAVE_FUNCTION, {
            "p_competencia": month.isoformat(),
            "p_registros": payload,
        })
        try:
            return int(data or 0)
        except (TypeError, ValueError) as error:
            raise DataAccessError("A Data API não confirmou o salvamento.") from error

    def save_campaign(self, records: list[dict], identity: Identity) -> int:
        """Salva todas as competências em uma única transação no Supabase."""
        if not identity.can_edit:
            raise PermissionDenied(f"Somente {' e '.join(EDITOR_EMAILS)} podem salvar alterações.")
        # A chave composta impede que duas linhas para a mesma região/mês
        # cheguem ao banco com versões potencialmente contraditórias.
        grouped: dict[date, list[dict]] = {}
        seen: set[tuple[date, str]] = set()
        for record in records:
            month = record.get("competencia")
            if not isinstance(month, date):
                raise ValueError("Competência inválida. Recarregue os dados.")
            validate_month(month)
            region = record.get("regiao")
            key = (month, str(region))
            if key in seen:
                raise ValueError("A lista de regiões foi alterada. Recarregue os dados.")
            seen.add(key)
            grouped.setdefault(month, []).append(record)

        payload = []
        for month, rows in grouped.items():
            for row in self._validate_rows(rows):
                payload.append({"competencia": month.isoformat(), **row})
        data = self._rpc(SAVE_CAMPAIGN_FUNCTION, {"p_registros": payload})
        try:
            return int(data or 0)
        except (TypeError, ValueError) as error:
            raise DataAccessError("A Data API não confirmou o salvamento.") from error
