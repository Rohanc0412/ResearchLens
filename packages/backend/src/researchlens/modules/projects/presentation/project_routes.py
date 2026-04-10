from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from researchlens.modules.projects.application import (
    CreateProjectCommand,
    CreateProjectUseCase,
    DeleteProjectCommand,
    DeleteProjectUseCase,
    ListProjectsQuery,
    ListProjectsUseCase,
    RenameProjectCommand,
    RenameProjectUseCase,
)
from researchlens.modules.projects.presentation.dependencies import (
    RequestActor,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_list_projects_use_case,
    get_rename_project_use_case,
    get_request_actor,
)
from researchlens.modules.projects.presentation.schemas import (
    CreateProjectRequest,
    ProjectResponse,
    RenameProjectRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])
RequestActorDep = Annotated[RequestActor, Depends(get_request_actor)]
CreateProjectUseCaseDep = Annotated[CreateProjectUseCase, Depends(get_create_project_use_case)]
ListProjectsUseCaseDep = Annotated[ListProjectsUseCase, Depends(get_list_projects_use_case)]
RenameProjectUseCaseDep = Annotated[RenameProjectUseCase, Depends(get_rename_project_use_case)]
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


@router.patch("/{project_id}", response_model=ProjectResponse)
async def rename_project(
    project_id: UUID,
    payload: RenameProjectRequest,
    actor: RequestActorDep,
    use_case: RenameProjectUseCaseDep,
) -> ProjectResponse:
    project = await use_case.execute(
        RenameProjectCommand(
            tenant_id=actor.tenant_id,
            actor_user_id=actor.user_id,
            project_id=project_id,
            new_name=payload.name,
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
