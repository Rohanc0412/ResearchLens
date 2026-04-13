from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from researchlens.modules.evidence.application import (
    ChunkDetailQuery,
    GetChunkDetailUseCase,
    GetRunEvidenceSummaryUseCase,
    GetSectionEvidenceTraceUseCase,
    GetSourceDetailUseCase,
    RunEvidenceQuery,
    SectionEvidenceQuery,
    SourceDetailQuery,
)
from researchlens.modules.evidence.presentation.dependencies import (
    RequestActorDep,
    get_chunk_detail_use_case,
    get_run_summary_use_case,
    get_section_trace_use_case,
    get_source_detail_use_case,
)
from researchlens.modules.evidence.presentation.response_models import (
    ChunkDetailResponse,
    RunEvidenceSummaryResponse,
    SectionEvidenceTraceResponse,
    SourceDetailResponse,
)
from researchlens.shared.errors import NotFoundError

router = APIRouter(tags=["evidence"])

RunSummaryDep = Annotated[GetRunEvidenceSummaryUseCase, Depends(get_run_summary_use_case)]
SectionTraceDep = Annotated[GetSectionEvidenceTraceUseCase, Depends(get_section_trace_use_case)]
ChunkDetailDep = Annotated[GetChunkDetailUseCase, Depends(get_chunk_detail_use_case)]
SourceDetailDep = Annotated[GetSourceDetailUseCase, Depends(get_source_detail_use_case)]


@router.get("/runs/{run_id}/evidence", response_model=RunEvidenceSummaryResponse)
async def get_run_evidence(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: RunSummaryDep,
) -> RunEvidenceSummaryResponse:
    summary = await use_case.execute(RunEvidenceQuery(tenant_id=actor.tenant_id, run_id=run_id))
    if summary is None:
        raise NotFoundError("Run evidence summary was not found.")
    return RunEvidenceSummaryResponse.model_validate(summary)


@router.get(
    "/runs/{run_id}/evidence/sections/{section_id}",
    response_model=SectionEvidenceTraceResponse,
)
async def get_section_evidence(
    run_id: UUID,
    section_id: str,
    actor: RequestActorDep,
    use_case: SectionTraceDep,
) -> SectionEvidenceTraceResponse:
    trace = await use_case.execute(
        SectionEvidenceQuery(tenant_id=actor.tenant_id, run_id=run_id, section_id=section_id)
    )
    if trace is None:
        raise NotFoundError("Section evidence trace was not found.")
    return SectionEvidenceTraceResponse.model_validate(trace)


@router.get("/evidence/chunks/{chunk_id}", response_model=ChunkDetailResponse)
async def get_chunk_detail(
    chunk_id: UUID,
    actor: RequestActorDep,
    use_case: ChunkDetailDep,
    context_window: int = Query(default=1, ge=0, le=5),
) -> ChunkDetailResponse:
    detail = await use_case.execute(
        ChunkDetailQuery(
            tenant_id=actor.tenant_id,
            chunk_id=chunk_id,
            context_window=context_window,
        )
    )
    if detail is None:
        raise NotFoundError("Evidence chunk was not found.")
    return ChunkDetailResponse.model_validate(detail)


@router.get("/evidence/sources/{source_id}", response_model=SourceDetailResponse)
async def get_source_detail(
    source_id: UUID,
    actor: RequestActorDep,
    use_case: SourceDetailDep,
) -> SourceDetailResponse:
    detail = await use_case.execute(
        SourceDetailQuery(tenant_id=actor.tenant_id, source_id=source_id)
    )
    if detail is None:
        raise NotFoundError("Evidence source was not found.")
    return SourceDetailResponse.model_validate(detail)
