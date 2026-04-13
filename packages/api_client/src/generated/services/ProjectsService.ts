/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CreateProjectRequest } from '../models/CreateProjectRequest';
import type { ProjectResponse } from '../models/ProjectResponse';
import type { UpdateProjectRequest } from '../models/UpdateProjectRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProjectsService {
    /**
     * List Projects
     * @returns ProjectResponse Successful Response
     * @throws ApiError
     */
    public static listProjectsProjectsGet(): CancelablePromise<Array<ProjectResponse>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/projects',
        });
    }
    /**
     * Create Project
     * @param requestBody
     * @returns ProjectResponse Successful Response
     * @throws ApiError
     */
    public static createProjectProjectsPost(
        requestBody: CreateProjectRequest,
    ): CancelablePromise<ProjectResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/projects',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Project
     * @param projectId
     * @returns ProjectResponse Successful Response
     * @throws ApiError
     */
    public static getProjectProjectsProjectIdGet(
        projectId: string,
    ): CancelablePromise<ProjectResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Project
     * @param projectId
     * @param requestBody
     * @returns ProjectResponse Successful Response
     * @throws ApiError
     */
    public static updateProjectProjectsProjectIdPatch(
        projectId: string,
        requestBody: UpdateProjectRequest,
    ): CancelablePromise<ProjectResponse> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Project
     * @param projectId
     * @returns void
     * @throws ApiError
     */
    public static deleteProjectProjectsProjectIdDelete(
        projectId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
