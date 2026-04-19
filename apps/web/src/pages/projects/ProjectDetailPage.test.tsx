import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { vi } from "vitest";

import type { ConversationLaunchState } from "../../entities/chat/chat.types";
import { ProjectDetailPage } from "./ProjectDetailPage";

const useProjectQueryMock = vi.fn();
const useConversationsQueryMock = vi.fn();
const useCreateConversationMutationMock = vi.fn();
const createConversationMock = vi.fn();

vi.mock("../../entities/project/project.api", () => ({
  useProjectQuery: () => useProjectQueryMock(),
}));

vi.mock("../../entities/conversation/conversation.api", () => ({
  useConversationsQuery: () => useConversationsQueryMock(),
  useCreateConversationMutation: () => useCreateConversationMutationMock(),
}));

function LaunchStatePreview() {
  const location = useLocation();
  const state = (location.state ?? {}) as ConversationLaunchState;
  return (
    <div data-testid="launch-state">
      {JSON.stringify({
        pathname: location.pathname,
        initialMessage: state.initialMessage ?? null,
        runPipeline: state.runPipeline ?? null,
      })}
    </div>
  );
}

function renderProjectDetailPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/projects/project-1"]}>
        <Routes>
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route
            path="/projects/:projectId/conversations/:conversationId"
            element={<LaunchStatePreview />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  sessionStorage.clear();
  createConversationMock.mockReset();
  useProjectQueryMock.mockReturnValue({
    data: { id: "project-1", name: "Alpha" },
  });
  useConversationsQueryMock.mockReturnValue({
    data: [],
  });
  useCreateConversationMutationMock.mockReturnValue({
    mutateAsync: createConversationMock,
    isPending: false,
  });
  createConversationMock.mockResolvedValue({ id: "conversation-1" });
});

test("starts a chat by navigating with the initial message state", async () => {
  const user = userEvent.setup();

  renderProjectDetailPage();

  await user.type(
    screen.getByLabelText("Research question"),
    "Summarize current biomarker work.",
  );
  await user.click(screen.getByRole("button", { name: "Start chat" }));

  await waitFor(() =>
    expect(createConversationMock).toHaveBeenCalledWith({
      title: "Summarize current biomarker work.",
    }),
  );
  await waitFor(() =>
    expect(screen.getByTestId("launch-state")).toHaveTextContent(
      '"initialMessage":"Summarize current biomarker work."',
    ),
  );
  expect(screen.getByTestId("launch-state")).toHaveTextContent(
    '"/projects/project-1/conversations/conversation-1"',
  );
  expect(screen.getByTestId("launch-state")).toHaveTextContent(
    '"runPipeline":false',
  );
});

test("starts report mode by navigating with runPipeline state", async () => {
  const user = userEvent.setup();

  renderProjectDetailPage();

  await user.type(
    screen.getByLabelText("Research question"),
    "Compare the latest cancer biomarker papers.",
  );
  await user.click(screen.getByRole("button", { name: "Run research report" }));

  await waitFor(() =>
    expect(createConversationMock).toHaveBeenCalledWith({
      title: "Compare the latest cancer biomarker papers.",
    }),
  );
  await waitFor(() =>
    expect(screen.getByTestId("launch-state")).toHaveTextContent(
      '"runPipeline":true',
    ),
  );
  expect(screen.getByTestId("launch-state")).toHaveTextContent(
    '"initialMessage":"Compare the latest cancer biomarker papers."',
  );
});
