"""Registros manuais de adiantamento, com autorização e controle de concorrência."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from sqlalchemy import (
    JSON, Boolean, Column, Date, DateTime, Integer, MetaData, Numeric, String,
    Table, Text, and_, func, insert, select, update,
)
from sqlalchemy.exc import IntegrityError

EDITOR_EMAILS = ("lais.vendrasco@ambar.tech", "leonardo.watanabe@ambar.tech")
SCHEMA = "comercial_marts"
FIELDS = ("semana_1_32", "semana_2_56", "semana_3_80")
metadata = MetaData(schema=SCHEMA)
registros = Table(
    "campanha_polar_adiantamento", metadata,
    Column("competencia", Date, primary_key=True),
    Column("regiao", Text, primary_key=True),
    *(Column(field, Boolean, nullable=False) for field in FIELDS),
    Column("observacao", Text, nullable=False),
    Column("versao", Integer, nullable=False),
    Column("atualizado_em", DateTime(timezone=True), nullable=False),
    Column("atualizado_por", String(320), nullable=False),
    Column("usuario_id", Text, nullable=False),
)
historico = Table(
    "campanha_polar_adiantamento_historico", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("competencia", Date, nullable=False),
    Column("regiao", Text, nullable=False),
    Column("versao", Integer, nullable=False),
    Column("anterior", JSON),
    Column("novo", JSON, nullable=False),
    Column("alterado_em", DateTime(timezone=True), nullable=False),
    Column("alterado_por", String(320), nullable=False),
    Column("usuario_id", Text, nullable=False),
)
metas_comerciais = Table(
    "metas_comerciais", metadata,
    Column("data", Date, primary_key=True),
    Column("regiao", Text, primary_key=True),
    Column("time", Text, nullable=False),
    Column("meta", Numeric(14, 2), nullable=False),
)


class PermissionDenied(ValueError):
    pass


class ConcurrentChange(ValueError):
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
        return bool(self.user_id and self.email in EDITOR_EMAILS)


def validate_month(month: date):
    if not isinstance(month, date) or month.day != 1 or month.year != 2026 or month.month not in (9, 10, 11, 12):
        raise ValueError("Escolha uma competência de setembro a dezembro de 2026.")


def blank_record(region: str):
    return {
        "regiao": region, **{field: False for field in FIELDS},
        "observacao": "", "versao": 0, "atualizado_em": None,
        "atualizado_por": "", "usuario_id": "",
    }


class Repository:
    def __init__(self, engine):
        self.engine = engine

    def region_names(self, month: date):
        """Regiões participantes são derivadas das metas válidas da competência."""
        validate_month(month)
        region = func.trim(metas_comerciais.c.regiao)
        team = func.upper(func.trim(metas_comerciais.c.time))
        statement = (
            select(region.label("regiao"))
            .where(
                metas_comerciais.c.data == month,
                metas_comerciais.c.meta > 0,
                region.is_not(None),
                region != "",
                team.in_(("CANAIS", "TIME NORTE", "TIME SUL")),
            )
            .distinct()
            .order_by(region)
        )
        with self.engine.connect() as connection:
            return list(connection.execute(statement).scalars())

    def goal_rows(self, month: date):
        """Retorna as metas das regiões participantes para compor o painel mensal."""
        validate_month(month)
        region = func.trim(metas_comerciais.c.regiao)
        team = func.trim(metas_comerciais.c.time)
        normalized_team = func.upper(team)
        statement = (
            select(
                region.label("regiao"),
                team.label("time"),
                metas_comerciais.c.meta.label("meta"),
            )
            .where(
                metas_comerciais.c.data == month,
                metas_comerciais.c.meta > 0,
                region.is_not(None),
                region != "",
                normalized_team.in_(("CANAIS", "TIME NORTE", "TIME SUL")),
            )
            .order_by(region)
        )
        with self.engine.connect() as connection:
            source = connection.execute(statement).mappings()
            combined: dict[str, dict] = {}
            for row in source:
                item = combined.setdefault(row["regiao"], {
                    "regiao": row["regiao"], "time": row["time"], "meta": 0,
                })
                item["meta"] += row["meta"] or 0
                if item["time"] != row["time"]:
                    item["time"] = "Múltiplos times"
        return list(combined.values())

    def load(self, month: date):
        validate_month(month)
        regions = self.region_names(month)
        with self.engine.connect() as connection:
            saved = {
                row["regiao"]: dict(row)
                for row in connection.execute(select(registros).where(registros.c.competencia == month)).mappings()
            }
        return [saved.get(region, blank_record(region)) for region in regions]

    def save(self, month: date, rows: list[dict], identity: Identity):
        # Não depender da visibilidade do botão nem de uma coluna enviada pelo editor.
        if not identity.can_edit:
            raise PermissionDenied(f"Somente {' e '.join(EDITOR_EMAILS)} podem salvar alterações.")
        validate_month(month)
        allowed = set(self.region_names(month))
        seen = set()
        for row in rows:
            region = row.get("regiao")
            if region not in allowed or region in seen:
                raise ValueError("A lista de regiões foi alterada. Recarregue os dados.")
            seen.add(region)
            if any(type(row.get(field)) is not bool for field in FIELDS):
                raise ValueError("Preencha os atingimentos com os checks da tabela.")
            if type(row.get("versao")) is not int or row["versao"] < 0:
                raise ValueError("Versão inválida. Recarregue os dados.")
            if not isinstance(row.get("observacao"), str) or len(row["observacao"]) > 2000:
                raise ValueError("A observação deve ter até 2.000 caracteres.")
        changed = 0
        try:
            with self.engine.begin() as connection:
                for row in rows:
                    key = and_(registros.c.competencia == month, registros.c.regiao == row["regiao"])
                    old = connection.execute(select(registros).where(key)).mappings().first()
                    old_version = old["versao"] if old else 0
                    if row["versao"] != old_version:
                        raise ConcurrentChange("Os registros mudaram em outra sessão. Recarregue antes de salvar.")
                    values = {field: row[field] for field in (*FIELDS, "observacao")}
                    previous = {field: old[field] for field in values} if old else None
                    if previous == values:
                        continue
                    now = datetime.now(timezone.utc)
                    changes = dict(values, versao=old_version + 1, atualizado_em=now,
                                   atualizado_por=identity.email, usuario_id=identity.user_id)
                    if old:
                        result = connection.execute(update(registros).where(
                            key, registros.c.versao == old_version).values(**changes))
                        if result.rowcount != 1:
                            raise ConcurrentChange("Os registros mudaram em outra sessão. Recarregue antes de salvar.")
                    else:
                        connection.execute(insert(registros).values(
                            competencia=month, regiao=row["regiao"], **changes))
                    connection.execute(insert(historico).values(
                        competencia=month, regiao=row["regiao"], versao=old_version + 1,
                        anterior=previous, novo=values, alterado_em=now,
                        alterado_por=identity.email, usuario_id=identity.user_id))
                    changed += 1
        except IntegrityError as error:
            raise ConcurrentChange("Os registros mudaram em outra sessão. Recarregue antes de salvar.") from error
        return changed
