from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from researchlens.modules.projects.application import (
    CreateProjectCommand,
    CreateProjectUseCase,
    DeleteProjectCommand,
    DeleteProjectUseCase,
    GetProjectQuery,
    GetProjectUseCase,
    ListProjectsQuery,
    ListProjectsUseCase,
    UpdateProjectMetadataCommand,
    UpdateProjectMetadataUseCase,
)
from researchlens.modules.projects.presentation.dependencies import (
    RequestActor,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_get_project_use_case,
    get_list_projects_use_case,
    get_request_actor,
    get_update_project_metadata_use_case,
)
from researchlens.modules.projects.presentation.schemas import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
CreateProjectUseCaseDep = Annotated[CreateProjectUseCase, Depends(get_create_project_use_case)]
ListProjectsUseCaseDep = Annotated[ListProjectsUseCase, Depends(get_list_projects_use_case)]
GetProjectUseCaseDep = Annotated[GetProjectUseCase, Depends(get_get_project_use_case)]
UpdateProjectUseCaseDep = Annotated[
    UpdateProjectMetadataUseCase,
    Depends(get_update_project_metadata_use_case),
]
DeleteProjectUseCaseDep = Annotated[DeleteProjectUseCase, Depends(get_delete_project_use_case)]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: CreateProjectRequest,
    actor: RequestActorDep,
    use_case: CreateProjectUseCaseDep,
) -> ProjectResponse:
    project = await use_case.execute(
        CreateProjectCommand(
            tenant_id=actor.tenant_id,
            actor_user_id=actor.user_id,
            name=payload.name,
            description=payload.description,
        )
    )
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    actor: RequestActorDep,
    use_case: ListProjectsUseCaseDep,
) -> list[ProjectResponse]:
    projects = await use_case.execute(ListProjectsQuery(tenant_id=actor.tenant_id))
    return [ProjectResponse.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    actor: RequestActorDep,
    use_case: GetProjectUseCaseDep,
) -> ProjectResponse:
    project = await use_case.execute(
        GetProjectQuery(tenant_id=actor.tenant_id, project_id=project_id)
    )
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: UpdateProjectRequest,
    actor: RequestActorDep,
    use_case: UpdateProjectUseCaseDep,
) -> ProjectResponse:
    project = await use_case.execute(
        UpdateProjectMetadataCommand(
            tenant_id=actor.tenant_id,
            actor_user_id=actor.user_id,
            project_id=project_id,
            new_name=payload.name,
            description=payload.description,
            description_provided="description" in payload.model_fields_set,
        )
    )
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    actor: RequestActorDep,
    use_case: DeleteProjectUseCaseDep,
) -> Response:
    await use_case.execute(
        DeleteProjectCommand(
            tenant_id=actor.tenant_id,
            actor_user_id=actor.user_id,
            project_id=project_id,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
