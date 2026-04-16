import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { ProjectsPage } from "./ProjectsPage";

const useProjectsQueryMock = vi.fn();
const useCreateProjectMutationMock = vi.fn();

vi.mock("../../entities/project/project.api", async () => {
  const actual = await vi.importActual<typeof import("../../entities/project/project.api")>(
    "../../entities/project/project.api",
  );

  return {
    ...actual,
    useCreateProjectMutation: () => useCreateProjectMutationMock(),
    useProjectsQuery: () => useProjectsQueryMock(),
  };
});

function renderProjectsPage(path = "/projects") {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/projects" element={<ProjectsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  useProjectsQueryMock.mockReturnValue({
    data: [],
    isError: false,
    isLoading: false,
  });
  useCreateProjectMutationMock.mockReturnValue({
    error: null,
    isPending: false,
    mutateAsync: vi.fn(),
  });
});

test("opens the create dialog when the legacy new-project query flag is present", () => {
  renderProjectsPage("/projects?new=1");

  expect(screen.getByRole("dialog")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "New Project" })).toBeInTheDocument();
});

test("removes the dialog when the user closes it", async () => {
  renderProjectsPage("/projects?new=1");
  const user = userEvent.setup();

  await user.click(screen.getByRole("button", { name: "Close dialog" }));

  await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
});
