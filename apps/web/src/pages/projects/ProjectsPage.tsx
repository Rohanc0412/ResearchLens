import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { useProjectsQuery } from "../../entities/project/project.api";
import { CreateProjectDialog } from "../../features/create_project/CreateProjectDialog";
import { Button } from "../../shared/ui/Button";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Page } from "../../shared/ui/Page";

export function ProjectsPage() {
  const projects = useProjectsQuery();
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const dialogOpen = searchParams.get("new") === "1";
  const visibleProjects = (projects.data ?? []).filter((project) =>
    `${project.name} ${project.description ?? ""}`.toLowerCase().includes(search.toLowerCase()),
  );
  const openDialog = () => setSearchParams({ new: "1" });
  const closeDialog = () => setSearchParams({});

  return (
    <Page
      eyebrow=""
      title="Projects"
      subtitle="Create and manage research projects."
      actions={
        <Button variant="primary" onClick={openDialog}>
          <span aria-hidden="true">+</span>
          New Project
        </Button>
      }
    >
      <label className="project-search">
        <span aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="m20 20-4.2-4.2" />
            <circle cx="11" cy="11" r="6.25" />
          </svg>
        </span>
        <input
          aria-label="Search projects"
          placeholder="Search projects..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>

      {!projects.isLoading && (projects.data?.length ?? 0) === 0 ? (
        <EmptyState
          icon="folder"
          title="No projects yet"
          body="Create your first project to start research runs."
          action={
            <Button variant="primary" onClick={openDialog}>
              <span aria-hidden="true">+</span>
              New Project
            </Button>
          }
        />
      ) : (
        <div className="project-table" role="table" aria-label="Projects">
          <div className="project-table__head" role="row">
            <span role="columnheader">Name</span>
            <span role="columnheader">Created</span>
            <span role="columnheader">Last Run</span>
            <span aria-hidden="true" />
          </div>
          <div className="project-table__body">
            {visibleProjects.map((project) => (
              <Link
                key={project.id}
                className="project-table__row"
                to={`/projects/${project.id}`}
                role="row"
              >
                <strong role="cell">{project.name}</strong>
                <span className="meta-line" role="cell">
                  {new Date(project.created_at).toLocaleString()}
                </span>
                <span className="meta-line" role="cell">
                  -
                </span>
                <span className="project-table__open" role="cell">
                  Open -&gt;
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
      <CreateProjectDialog open={dialogOpen} onClose={closeDialog} />
    </Page>
  );
}
