import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { vi } from "vitest";

import { ConversationPage } from "./ConversationPage";

const useConversationQueryMock = vi.fn();
const useProjectQueryMock = vi.fn();
const useChatMessagesQueryMock = vi.fn();
const useSendChatMessageMutationMock = vi.fn();
const useCreateRunMutationMock = vi.fn();
const sendChatMutateAsyncMock = vi.fn();
const createRunMutateAsyncMock = vi.fn();
let sendChatCallbacks: { onStatus?: () => void } | undefined;

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

function RouterStatePreview() {
  const location = useLocation();
  return <div data-testid="router-state">{JSON.stringify(location.state ?? {})}</div>;
}

function renderConversationPage(state?: Record<string, unknown>) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter
        initialEntries={[
          {
            pathname: "/projects/project-1/conversations/conversation-1",
            state,
          },
        ]}
      >
        <Routes>
          <Route
            path="/projects/:projectId/conversations/:conversationId"
            element={
              <>
                <ConversationPage />
                <RouterStatePreview />
              </>
            }
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
  sendChatCallbacks = undefined;
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
  useSendChatMessageMutationMock.mockImplementation(
    (_conversationId: string, callbacks?: { onStatus?: () => void }) => {
      sendChatCallbacks = callbacks;
      return { mutateAsync: sendChatMutateAsyncMock };
    },
  );
  useCreateRunMutationMock.mockReturnValue({
    mutateAsync: createRunMutateAsyncMock,
  });
  sendChatMutateAsyncMock.mockResolvedValue(buildResponse());
  createRunMutateAsyncMock.mockResolvedValue({
    run: { id: "run-1" },
  });
});

test("auto-sends the initial message once and clears router state", async () => {
  renderConversationPage({ initialMessage: "Prompt", runPipeline: false });

  await waitFor(() =>
    expect(sendChatMutateAsyncMock).toHaveBeenCalledWith({
      conversation_id: "conversation-1",
      message: "Prompt",
      client_message_id: expect.any(String),
      llm_model: "gpt-5-nano",
      force_pipeline: false,
    }),
  );
  await waitFor(() => expect(screen.getByTestId("router-state")).toHaveTextContent("{}"));
  expect(sendChatMutateAsyncMock).toHaveBeenCalledTimes(1);
  expect(createRunMutateAsyncMock).not.toHaveBeenCalled();
});

test("shows web-search status during an initial streamed send", async () => {
  let releaseSend: (() => void) | undefined;
  sendChatMutateAsyncMock.mockImplementation(async () => {
    sendChatCallbacks?.onStatus?.();
    await new Promise<void>((resolve) => {
      releaseSend = resolve;
    });
    return buildResponse("Prompt");
  });

  renderConversationPage({ initialMessage: "Prompt", runPipeline: false });

  await waitFor(() => expect(screen.getByText("Searching the web...")).toBeInTheDocument());
  releaseSend?.();
  await waitFor(() => expect(sendChatMutateAsyncMock).toHaveBeenCalledTimes(1));
});

test("creates a run when report mode is restored from router state", async () => {
  renderConversationPage({ initialMessage: "Prompt", runPipeline: true });

  await waitFor(() =>
    expect(sendChatMutateAsyncMock).toHaveBeenCalledWith({
      conversation_id: "conversation-1",
      message: "Prompt",
      client_message_id: expect.any(String),
      llm_model: "gpt-5-nano",
      force_pipeline: true,
    }),
  );
  await waitFor(() =>
    expect(createRunMutateAsyncMock).toHaveBeenCalledWith({
      request_text: "Prompt",
      source_message_id: "user-1",
    }),
  );
});
