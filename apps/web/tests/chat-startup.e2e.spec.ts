import { expect, test } from "@playwright/test";

const user = {
  user_id: "user-1",
  username: "casey",
  email: "casey@example.com",
  tenant_id: "tenant-1",
  roles: ["user"],
};

async function json(
  route: Parameters<Parameters<typeof test>[1]>[0]["route"],
  body: unknown,
  status = 200,
) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

test("project startup sends the first chat turn through /send", async ({ page }) => {
  let createConversationCalls = 0;
  let sendCalls = 0;
  let messagePostCalls = 0;
  let runCreateCalls = 0;
  let persistedMessages: Array<Record<string, unknown>> = [];

  await page.route("http://localhost:8017/auth/refresh", async (route) => {
    await json(route, {
      access_token: "token-1",
      token_type: "bearer",
      expires_in: 900,
      user,
    });
  });

  await page.route("http://localhost:8017/projects", async (route) => {
    await json(route, [
      {
        id: "project-1",
        tenant_id: "tenant-1",
        name: "Alpha",
        description: "Primary research project",
        created_by: "user-1",
        created_at: "2026-04-13T10:00:00Z",
        updated_at: "2026-04-13T10:00:00Z",
      },
    ]);
  });

  await page.route("http://localhost:8017/projects/project-1", async (route) => {
    await json(route, {
      id: "project-1",
      tenant_id: "tenant-1",
      name: "Alpha",
      description: "Primary research project",
      created_by: "user-1",
      created_at: "2026-04-13T10:00:00Z",
      updated_at: "2026-04-13T10:00:00Z",
    });
  });

  await page.route(
    /http:\/\/(localhost|127\.0\.0\.1):8017\/projects\/project-1\/conversations(\?.*)?$/,
    async (route) => {
      if (route.request().method() === "POST") {
        createConversationCalls += 1;
        await json(route, {
          id: "conversation-1",
          tenant_id: "tenant-1",
          project_id: "project-1",
          created_by_user_id: "user-1",
          title: "Summarize current biomarker work.",
          created_at: "2026-04-13T10:05:00Z",
          updated_at: "2026-04-13T10:05:00Z",
          last_message_at: null,
        });
        return;
      }

      await json(route, { items: [], next_cursor: null });
    },
  );

  await page.route(
    /http:\/\/(localhost|127\.0\.0\.1):8017\/conversations\/conversation-1$/,
    async (route) => {
      await json(route, {
        id: "conversation-1",
        tenant_id: "tenant-1",
        project_id: "project-1",
        created_by_user_id: "user-1",
        title: "Summarize current biomarker work.",
        created_at: "2026-04-13T10:05:00Z",
        updated_at: "2026-04-13T10:05:00Z",
        last_message_at: "2026-04-13T10:06:00Z",
      });
    },
  );

  await page.route(
    /http:\/\/(localhost|127\.0\.0\.1):8017\/conversations\/conversation-1\/messages$/,
    async (route) => {
      if (route.request().method() === "POST") {
        messagePostCalls += 1;
      }
      await json(route, persistedMessages);
    },
  );

  await page.route(
    /http:\/\/(localhost|127\.0\.0\.1):8017\/conversations\/conversation-1\/runs$/,
    async (route) => {
      runCreateCalls += 1;
      await json(route, { detail: "Should not create a run" }, 500);
    },
  );

  await page.route(
    /http:\/\/(localhost|127\.0\.0\.1):8017\/conversations\/[^/]+\/send(\?.*)?$/,
    async (route) => {
      sendCalls += 1;
      expect(route.request().postDataJSON()).toEqual({
        message: "Summarize current biomarker work.",
        client_message_id: expect.any(String),
        llm_model: "gpt-5-nano",
        force_pipeline: false,
      });
      persistedMessages = [
        {
          id: "user-1",
          tenant_id: "tenant-1",
          conversation_id: "conversation-1",
          role: "user",
          type: "chat",
          content_text: "Summarize current biomarker work.",
          content_json: null,
          metadata_json: null,
          created_at: "2026-04-13T10:06:00Z",
          client_message_id: "client-1",
        },
        {
          id: "assistant-1",
          tenant_id: "tenant-1",
          conversation_id: "conversation-1",
          role: "assistant",
          type: "chat",
          content_text: "Found a concise answer.",
          content_json: null,
          metadata_json: null,
          created_at: "2026-04-13T10:06:01Z",
          client_message_id: null,
        },
      ];
      await json(route, {
        conversation_id: "conversation-1",
        user_message: {
          id: "user-1",
          role: "user",
          type: "chat",
          content_text: "Summarize current biomarker work.",
          content_json: null,
          created_at: "2026-04-13T10:06:00Z",
          client_message_id: "client-1",
        },
        assistant_message: {
          id: "assistant-1",
          role: "assistant",
          type: "chat",
          content_text: "Found a concise answer.",
          content_json: null,
          created_at: "2026-04-13T10:06:01Z",
          client_message_id: null,
        },
        pending_action: null,
        idempotent_replay: false,
      });
    },
  );

  await page.goto("/projects/project-1");
  await page.getByLabel("Research question").fill("Summarize current biomarker work.");
  await page.getByRole("button", { name: "Start chat" }).click();

  await expect.poll(() => createConversationCalls).toBe(1);
  await expect(
    page.getByRole("heading", { name: "Summarize current biomarker work." }),
  ).toBeVisible();
  await expect.poll(() => sendCalls).toBe(1);
  await expect(page.getByText("Found a concise answer.")).toBeVisible();

  expect(sendCalls).toBe(1);
  expect(messagePostCalls).toBe(0);
  expect(runCreateCalls).toBe(0);
});
