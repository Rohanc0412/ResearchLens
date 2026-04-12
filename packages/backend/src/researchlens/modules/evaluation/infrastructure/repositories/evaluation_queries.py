from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchlens.modules.evaluation.infrastructure.rows import EvaluationPassRow


async def latest_completed_pass(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> EvaluationPassRow | None:
    return cast(
        EvaluationPassRow | None,
        await session.scalar(
        select(EvaluationPassRow)
        .where(
            EvaluationPassRow.tenant_id == tenant_id,
            EvaluationPassRow.run_id == run_id,
            EvaluationPassRow.status == "completed",
        )
        .order_by(EvaluationPassRow.pass_index.desc())
        .limit(1)
        ),
    )
