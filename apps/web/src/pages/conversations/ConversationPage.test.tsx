import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { ConversationPage } from "./ConversationPage";

const useConversationQueryMock = vi.fn();
const useProjectQueryMock = vi.fn();
const useChatMessagesQueryMock = vi.fn();
const useSendChatMessageMutationMock = vi.fn();
const useCreateRunMutationMock = vi.fn();
const sendChatMutateAsyncMock = vi.fn();
const createRunMutateAsyncMock = vi.fn();

vi.mock("../../entities/conversation/conversation.api", () => ({
  useConversationQuery: () => useConversationQueryMock(),
}));

vi.mock("../../entities/project/project.api", () => ({
  useProjectQuery: () => useProjectQueryMock(),
}));

vi.mock("../../entities/chat/chat.api", () => ({
  useChatMessagesQuery: () => useChatMessagesQueryMock(),
  useSendChatMessageMutation: (conversationId: string, callbacks?: { onStatus?: () => void }) =>
    useSendChatMessageMutationMock(conversationId, callbacks),
}));

vi.mock("../../entities/run/run.api", () => ({
  useCreateRunMutation: () => useCreateRunMutationMock(),
}));

vi.mock("../../widgets/conversation_shell/ChatViewHeader", () => ({
  ChatViewHeader: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("../../widgets/conversation_shell/ReportPane", () => ({
  ReportPane: () => <div>Report pane</div>,
}));

function renderConversationPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={["/projects/project-1/conversations/conversation-1"]}>
        <Routes>
          <Route
            path="/projects/:projectId/conversations/:conversationId"
            element={<ConversationPage />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function buildResponse(prompt = "Prompt") {
  return {
    assistant_message: {
      id: "assistant-1",
      role: "assistant",
      type: "run_started",
      content_text: "Starting the research pipeline.",
      content_json: { question: prompt, status: "queued" },
      created_at: "2026-04-17T15:00:00Z",
      client_message_id: null,
    },
    pending_action: {
      type: "start_research_run",
      prompt,
    },
    user_message: {
      id: "user-1",
      role: "user",
      type: "chat",
      content_text: prompt,
      content_json: null,
      created_at: "2026-04-17T15:00:00Z",
      client_message_id: "client-1",
    },
    idempotent_replay: false,
  };
}

beforeEach(() => {
  sessionStorage.clear();
  sendChatMutateAsyncMock.mockReset();
  createRunMutateAsyncMock.mockReset();
  useConversationQueryMock.mockReturnValue({
    data: { id: "conversation-1", title: "Cancer biomarkers" },
  });
  useProjectQueryMock.mockReturnValue({
    data: { id: "project-1", name: "Alpha" },
  });
  useChatMessagesQueryMock.mockReturnValue({
    data: [],
  });
  useSendChatMessageMutationMock.mockReturnValue({
    mutateAsync: sendChatMutateAsyncMock,
  });
  useCreateRunMutationMock.mockReturnValue({
    mutateAsync: createRunMutateAsyncMock,
  });
  sendChatMutateAsyncMock.mockResolvedValue(buildResponse());
  createRunMutateAsyncMock.mockResolvedValue({
    run: { id: "run-1" },
  });
});

test("does not create a run when research mode is not selected", async () => {
  const user = userEvent.setup();

  renderConversationPage();

  await user.type(screen.getByLabelText("Message input"), "Prompt");
  await user.click(screen.getByRole("button", { name: "Send message" }));

  await waitFor(() => expect(sendChatMutateAsyncMock).toHaveBeenCalled());
  expect(sendChatMutateAsyncMock).toHaveBeenCalledWith({
    conversation_id: "conversation-1",
    message: "Prompt",
    client_message_id: expect.any(String),
    llm_model: "gpt-5-nano",
    force_pipeline: false,
  });
  expect(createRunMutateAsyncMock).not.toHaveBeenCalled();
});

test("creates a run when the offered report action is selected", async () => {
  const user = userEvent.setup();
  useChatMessagesQueryMock.mockReturnValue({
    data: [
      {
        id: "offer-1",
        role: "assistant",
        type: "pipeline_offer",
        content_text: "Choose how to continue.",
        content_json: {
          offer: {
            actions: [
              { id: "run_pipeline", label: "Run research report" },
              { id: "quick_answer", label: "Quick answer" },
            ],
          },
        },
        created_at: "2026-04-17T15:00:00Z",
        client_message_id: null,
      },
    ],
  });

  renderConversationPage();

  await user.click(
    within(screen.getByRole("log", { name: "Chat messages" })).getByRole("button", {
      name: "Run research report",
    }),
  );

  await waitFor(() =>
    expect(createRunMutateAsyncMock).toHaveBeenCalledWith({
      request_text: "Prompt",
      source_message_id: "user-1",
    }),
  );
  expect(sendChatMutateAsyncMock).toHaveBeenCalledWith({
    conversation_id: "conversation-1",
    message: "__ACTION__:run_pipeline",
    client_message_id: expect.any(String),
    llm_model: "gpt-5-nano",
    force_pipeline: false,
  });
});

test("renders chat and report as separate panes", () => {
  renderConversationPage();

  const chatPane = document.querySelector(".legacy-conversation-shell__chat");
  const reportPane = document.querySelector(".legacy-conversation-shell__report");

  expect(chatPane).not.toBeNull();
  expect(chatPane?.querySelector('[role="log"][aria-label="Chat messages"]')).not.toBeNull();
  expect(chatPane?.querySelector(".legacy-conversation-shell__composer")).not.toBeNull();
  expect(reportPane).not.toBeNull();
  expect(reportPane).toHaveTextContent("Report pane");
});
