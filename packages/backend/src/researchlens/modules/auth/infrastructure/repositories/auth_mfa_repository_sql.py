from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.auth.domain import MfaFactor
from researchlens.modules.auth.infrastructure.repositories.auth_row_mappers import (
    mfa_factor_from_row,
)
from researchlens.modules.auth.infrastructure.rows import AuthMfaFactorRow


class SqlAlchemyMfaRepositoryMixin:
    _session: AsyncSession

    async def get_mfa_factors_for_user(self, *, user_id: UUID) -> list[MfaFactor]:
        rows = await self._session.scalars(
            select(AuthMfaFactorRow).where(AuthMfaFactorRow.user_id == user_id)
        )
        return [mfa_factor_from_row(row) for row in rows]

    async def get_mfa_factor(self, *, user_id: UUID, factor_type: str) -> MfaFactor | None:
        row = await self._session.scalar(
            select(AuthMfaFactorRow).where(
                AuthMfaFactorRow.user_id == user_id,
                AuthMfaFactorRow.factor_type == factor_type,
            )
        )
        return mfa_factor_from_row(row) if row else None

    async def add_mfa_factor(self, *, factor: MfaFactor) -> MfaFactor:
        row = AuthMfaFactorRow(
            id=factor.id,
            user_id=factor.user_id,
            tenant_id=factor.tenant_id,
            factor_type=factor.factor_type,
            secret=factor.secret,
            created_at=factor.created_at,
            enabled_at=factor.enabled_at,
            last_used_at=factor.last_used_at,
        )
        self._session.add(row)
        await self._session.flush()
        return mfa_factor_from_row(row)

    async def save_mfa_factor(self, *, factor: MfaFactor) -> None:
        row = await self._session.get(AuthMfaFactorRow, factor.id)
        if row is None:
            return
        row.secret = factor.secret
        row.created_at = factor.created_at
        row.enabled_at = factor.enabled_at
        row.last_used_at = factor.last_used_at

    async def delete_mfa_factor(self, *, factor_id: UUID) -> None:
        await self._session.execute(
            delete(AuthMfaFactorRow).where(AuthMfaFactorRow.id == factor_id)
        )
