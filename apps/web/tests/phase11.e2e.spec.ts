import { expect, test } from "@playwright/test";

const user = {
  user_id: "user-1",
  username: "casey",
  email: "casey@example.com",
  tenant_id: "tenant-1",
  roles: ["user"],
};

async function json(route: Parameters<Parameters<typeof test>[1]>[0]["route"], body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

test("login, session restore, and logout", async ({ page }) => {
  let refreshCount = 0;

  await page.route("http://127.0.0.1:8017/auth/refresh", async (route) => {
    refreshCount += 1;
    if (refreshCount === 1) {
      await json(route, { detail: "No session", code: "authentication_error" }, 401);
      return;
    }
    await json(route, {
      access_token: `token-${refreshCount}`,
      token_type: "bearer",
      expires_in: 900,
      user,
    });
  });
  await page.route("http://127.0.0.1:8017/auth/login", async (route) => {
    await json(route, {
      access_token: "token-login",
      token_type: "bearer",
      expires_in: 900,
      user,
    });
  });
  await page.route("http://127.0.0.1:8017/auth/logout", async (route) => {
    await json(route, { status: "ok" });
  });
  await page.route("http://127.0.0.1:8017/projects", async (route) => {
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

  await page.goto("/login");
  await page.getByLabel("Username or email").fill("casey");
  await page.getByLabel("Password").fill("CorrectHorse1!");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByText("Research workspace")).toBeVisible();

  await page.reload();
  await expect(page.getByText("Research workspace")).toBeVisible();

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page.getByText("Obsidian session access")).toBeVisible();
});

test("conversation flow, live run progress, and artifacts", async ({ page }) => {
  await page.route("http://127.0.0.1:8017/auth/refresh", async (route) => {
    await json(route, {
      access_token: "token-1",
      token_type: "bearer",
      expires_in: 900,
      user,
    });
  });
  await page.route("http://127.0.0.1:8017/projects", async (route) => {
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
  await page.route(/http:\/\/127\.0\.0\.1:8017\/projects\/project-1\/conversations(\?.*)?$/, async (route) => {
    await json(route, { items: [], next_cursor: null });
  });
  await page.route("http://127.0.0.1:8017/conversations/conversation-1", async (route) => {
    await json(route, {
      id: "conversation-1",
      tenant_id: "tenant-1",
      project_id: "project-1",
      created_by_user_id: "user-1",
      title: "Cancer biomarkers",
      created_at: "2026-04-13T10:00:00Z",
      updated_at: "2026-04-13T10:00:00Z",
      last_message_at: "2026-04-13T10:05:00Z",
    });
  });
  await page.route("http://127.0.0.1:8017/conversations/conversation-1/messages", async (route) => {
    if (route.request().method() === "GET") {
      await json(route, [
        {
          id: "message-1",
          tenant_id: "tenant-1",
          conversation_id: "conversation-1",
          role: "user",
          type: "text",
          content_text: "Review biomarkers for melanoma.",
          content_json: null,
          metadata_json: null,
          created_at: "2026-04-13T10:05:00Z",
          client_message_id: "client-1",
        },
      ]);
      return;
    }

    await json(route, {
      id: "message-2",
      tenant_id: "tenant-1",
      conversation_id: "conversation-1",
      role: "user",
      type: "text",
      content_text: "Summarize the findings.",
      content_json: null,
      metadata_json: null,
      created_at: "2026-04-13T10:06:00Z",
      client_message_id: "client-2",
      idempotent_replay: false,
    }, 201);
  });
  await page.route("http://127.0.0.1:8017/conversations/conversation-1/runs", async (route) => {
    await json(route, {
      run: {
        id: "run-1",
        project_id: "project-1",
        conversation_id: "conversation-1",
        status: "running",
        current_stage: "draft",
        output_type: "report",
        client_request_id: null,
        retry_count: 0,
        cancel_requested: false,
        created_at: "2026-04-13T10:06:00Z",
        updated_at: "2026-04-13T10:06:00Z",
        started_at: "2026-04-13T10:06:01Z",
        finished_at: null,
        failure_reason: null,
        error_code: null,
        last_event_number: 0,
        display_status: "Running",
        display_stage: "Drafting",
        can_stop: true,
        can_retry: false,
      },
      idempotent_replay: false,
    }, 201);
  });
  await page.route("http://127.0.0.1:8017/runs/run-1", async (route) => {
    await json(route, {
      id: "run-1",
      project_id: "project-1",
      conversation_id: "conversation-1",
      status: "succeeded",
      current_stage: "export",
      output_type: "report",
      client_request_id: null,
      retry_count: 0,
      cancel_requested: false,
      created_at: "2026-04-13T10:06:00Z",
      updated_at: "2026-04-13T10:06:20Z",
      started_at: "2026-04-13T10:06:01Z",
      finished_at: "2026-04-13T10:06:20Z",
      failure_reason: null,
      error_code: null,
      last_event_number: 2,
      display_status: "Completed",
      display_stage: "Exporting",
      can_stop: false,
      can_retry: true,
    });
  });
  await page.route(/http:\/\/127\.0\.0\.1:8017\/runs\/run-1\/events(\?.*)?$/, async (route) => {
    if (route.request().headers()["accept"]?.includes("text/event-stream")) {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          'event: checkpoint.written\nid: 1\ndata: {"run_id":"run-1","event_number":1,"event_type":"checkpoint.written","status":"running","stage":"draft","display_status":"Running","display_stage":"Drafting","message":"Draft section started","retry_count":0,"cancel_requested":false,"payload":null,"ts":"2026-04-13T10:06:05Z"}\n\n' +
          'event: run.succeeded\nid: 2\ndata: {"run_id":"run-1","event_number":2,"event_type":"run.succeeded","status":"succeeded","stage":"export","display_status":"Completed","display_stage":"Exporting","message":"Run completed successfully","retry_count":0,"cancel_requested":false,"payload":{"artifact_ids":["artifact-1"]},"ts":"2026-04-13T10:06:20Z"}\n\n',
      });
      return;
    }

    await json(route, []);
  });
  await page.route("http://127.0.0.1:8017/runs/run-1/artifacts", async (route) => {
    await json(route, [
      {
        id: "artifact-1",
        run_id: "run-1",
        kind: "report_markdown",
        filename: "report.md",
        media_type: "text/markdown",
        storage_backend: "local",
        byte_size: 128,
        sha256: "abc",
        created_at: "2026-04-13T10:06:20Z",
        manifest_id: "manifest-1",
      },
    ]);
  });
  await page.route("http://127.0.0.1:8017/runs/run-1/evidence", async (route) => {
    await json(route, {
      run_id: "run-1",
      project_id: "project-1",
      conversation_id: "conversation-1",
      section_count: 1,
      source_count: 1,
      chunk_count: 1,
      claim_count: 1,
      issue_count: 0,
      repaired_section_count: 0,
      unresolved_section_count: 0,
      latest_evaluation_pass_id: "eval-1",
      latest_repair_pass_id: null,
      artifact_count: 1,
      sections: [
        {
          section_id: "overview",
          title: "Overview",
          section_order: 1,
          repaired: false,
          issue_count: 0,
        },
      ],
    });
  });
  await page.route("http://127.0.0.1:8017/runs/run-1/evidence/sections/overview", async (route) => {
    await json(route, {
      section_id: "overview",
      section_title: "Overview",
      section_order: 1,
      canonical_text: "Overview body",
      canonical_summary: "Overview summary",
      repaired: false,
      latest_evaluation_result_id: "eval-section-1",
      repair_result_id: null,
      claims: [],
      issues: [],
      evidence_chunks: [
        {
          chunk_id: "chunk-1",
          source_id: "source-1",
          source_title: "Paper",
          chunk_index: 0,
          excerpt_text: "Evidence excerpt",
        },
      ],
      source_refs: [],
      unresolved_quality_findings: [],
    });
  });
  await page.route("http://127.0.0.1:8017/runs/run-1/evaluation", async (route) => {
    await json(route, {
      evaluation_pass_id: "eval-1",
      section_count: 1,
      evaluated_section_count: 1,
      issue_count: 0,
      sections_requiring_repair_count: 0,
      quality_pct: 96.5,
      unsupported_claim_rate: 0,
      pass_rate: 1,
      ragas_faithfulness_pct: 97.2,
      issues_by_type: {},
      repair_recommended: false,
      sections_requiring_repair: [],
    });
  });
  await page.route(/http:\/\/127\.0\.0\.1:8017\/runs\/run-1\/evaluation\/issues(\?.*)?$/, async (route) => {
    await json(route, []);
  });
  await page.route("http://127.0.0.1:8017/runs/run-1/repair", async (route) => {
    await json(route, null);
  });
  await page.route("http://127.0.0.1:8017/artifacts/artifact-1/download", async (route) => {
    await route.fulfill({
      status: 200,
      headers: {
        "Content-Type": "text/markdown",
        "Content-Disposition": 'attachment; filename="report.md"',
      },
      body: "# Report\n\nMelanoma biomarker summary.",
    });
  });

  await page.goto("/projects/project-1/conversations/conversation-1?runId=run-1");
  await expect(page.getByText("Cancer biomarkers")).toBeVisible();
  await expect(page.getByRole("link", { name: "View artifacts", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "View artifacts", exact: true }).click();
  await expect(page.getByText("Run outputs")).toBeVisible();

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("report.md");
});

test("auth expiration redirects back to login", async ({ page }) => {
  let refreshCount = 0;

  await page.route("http://127.0.0.1:8017/auth/refresh", async (route) => {
    refreshCount += 1;
    if (refreshCount === 1) {
      await json(route, {
        access_token: "token-1",
        token_type: "bearer",
        expires_in: 900,
        user,
      });
      return;
    }

    await json(route, { detail: "Expired", code: "authentication_error" }, 401);
  });
  await page.route("http://127.0.0.1:8017/projects", async (route) => {
    await json(route, { detail: "Expired", code: "authentication_error" }, 401);
  });

  await page.goto("/projects");
  await expect(page.getByText("Obsidian session access")).toBeVisible();
});
