import { useState } from "react";
import { Link } from "react-router-dom";

import { CreateProjectDialog } from "../../features/create_project/CreateProjectDialog";
import { useProjectsQuery } from "../../entities/project/project.api";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Page } from "../../shared/ui/Page";

export function ProjectsPage() {
  const projects = useProjectsQuery();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [search, setSearch] = useState("");
  const visibleProjects = (projects.data ?? []).filter((project) =>
    `${project.name} ${project.description ?? ""}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <Page
      eyebrow="Projects"
      title="Research workspace"
      subtitle="Projects anchor conversations, runs, evidence inspection, and final artifacts."
      actions={
        <Button variant="primary" onClick={() => setDialogOpen(true)}>
          New project
        </Button>
      }
    >
      <div className="toolbar">
        <input
          aria-label="Search projects"
          className="field__control toolbar__search"
          placeholder="Search projects"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <span className="meta-line">{visibleProjects.length} visible</span>
      </div>
      {!projects.isLoading && (projects.data?.length ?? 0) === 0 ? (
        <EmptyState
          title="No projects yet"
          body="Create your first project to start a conversation-driven research run."
          action={
            <Button variant="primary" onClick={() => setDialogOpen(true)}>
              Create project
            </Button>
          }
        />
      ) : (
        <div className="data-list">
          {visibleProjects.map((project) => (
            <Link key={project.id} className="data-row" to={`/projects/${project.id}`}>
              <Card interactive className="data-row__card" title={project.name} meta={project.description ?? "No description"}>
                <div className="meta-line">
                  Updated {new Date(project.updated_at).toLocaleString()}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
      <CreateProjectDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </Page>
  );
}
