import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { ProjectSidebar } from "./ProjectSidebar";

const useAuthMock = vi.fn();
const useProjectsQueryMock = vi.fn();
const useConversationsQueryMock = vi.fn();

vi.mock("../../app/providers/AuthProvider", () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock("../../entities/project/project.api", () => ({
  useProjectsQuery: () => useProjectsQueryMock(),
}));

vi.mock("../../entities/conversation/conversation.api", () => ({
  useConversationsQuery: (projectId: string) => useConversationsQueryMock(projectId),
}));

function renderSidebar(path = "/projects/project-1/conversations/conversation-1") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ProjectSidebar />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  useAuthMock.mockReturnValue({ logout: vi.fn() });
  useProjectsQueryMock.mockReturnValue({
    data: [{ id: "project-1", name: "Test" }],
    isError: false,
    isLoading: false,
  });
  useConversationsQueryMock.mockReturnValue({
    data: [{ id: "conversation-1", last_message_at: null, title: "First chat" }],
  });
});

test("shows the workspace and account labels when expanded", () => {
  renderSidebar();

  expect(screen.getByText("Workspace")).toBeInTheDocument();
  expect(screen.getByText("Recent Conversations")).toBeInTheDocument();
  expect(screen.getByText("Account")).toBeInTheDocument();
  expect(screen.getByText("New project")).toBeInTheDocument();
  expect(screen.getByText("Security")).toBeInTheDocument();
});

test("keeps navigation available after collapsing into the legacy icon rail", async () => {
  renderSidebar();
  const user = userEvent.setup();

  await user.click(screen.getByRole("button", { name: "Collapse sidebar" }));

  expect(screen.queryByText("Workspace")).not.toBeInTheDocument();
  expect(screen.getByTitle("New project")).toBeInTheDocument();
  expect(screen.getByTitle("Test")).toBeInTheDocument();
  expect(screen.getByTitle("Security")).toBeInTheDocument();
  expect(screen.getByTitle("Logout")).toBeInTheDocument();
});
