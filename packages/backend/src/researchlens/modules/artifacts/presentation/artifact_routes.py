from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from researchlens.modules.artifacts.application import (
    ArtifactQuery,
    DownloadArtifactUseCase,
    GetArtifactDetailUseCase,
    ListRunArtifactsUseCase,
)
from researchlens.modules.artifacts.presentation.dependencies import (
    RequestActorDep,
    get_artifact_detail_use_case,
    get_download_artifact_use_case,
    get_list_run_artifacts_use_case,
)
from researchlens.modules.artifacts.presentation.response_models import ArtifactResponse
from researchlens.shared.errors import NotFoundError

router = APIRouter(tags=["artifacts"])

ListArtifactsDep = Annotated[ListRunArtifactsUseCase, Depends(get_list_run_artifacts_use_case)]
GetArtifactDep = Annotated[GetArtifactDetailUseCase, Depends(get_artifact_detail_use_case)]
DownloadArtifactDep = Annotated[DownloadArtifactUseCase, Depends(get_download_artifact_use_case)]


@router.get("/runs/{run_id}/artifacts", response_model=tuple[ArtifactResponse, ...])
async def list_run_artifacts(
    run_id: UUID,
    actor: RequestActorDep,
    use_case: ListArtifactsDep,
) -> tuple[ArtifactResponse, ...]:
    artifacts = await use_case.execute(ArtifactQuery(tenant_id=actor.tenant_id, run_id=run_id))
    return tuple(ArtifactResponse.model_validate(item) for item in artifacts)


@router.get("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: UUID,
    actor: RequestActorDep,
    use_case: GetArtifactDep,
) -> ArtifactResponse:
    artifact = await use_case.execute(
        ArtifactQuery(tenant_id=actor.tenant_id, artifact_id=artifact_id)
    )
    if artifact is None:
        raise NotFoundError("Artifact was not found.")
    return ArtifactResponse.model_validate(artifact)


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(
    request: Request,
    artifact_id: UUID,
    actor: RequestActorDep,
    use_case: DownloadArtifactDep,
) -> Response:
    download = await use_case.execute(
        tenant_id=actor.tenant_id,
        actor_user_id=actor.user_id,
        artifact_id=artifact_id,
        request_id=request.headers.get("X-Request-ID"),
        user_agent=request.headers.get("User-Agent"),
    )
    return Response(
        content=download.content,
        media_type=download.media_type,
        headers={"Content-Disposition": f'attachment; filename="{download.filename}"'},
    )
