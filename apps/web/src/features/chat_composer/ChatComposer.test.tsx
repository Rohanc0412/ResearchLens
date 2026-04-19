import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ChatComposer } from "./ChatComposer";
import { CUSTOM_MODEL_VALUE } from "./chatComposer.constants";

function renderComposer(overrides?: Partial<ComponentProps<typeof ChatComposer>>) {
  return render(
    <ChatComposer
      draft=""
      isTyping={false}
      runPipelineArmed={false}
      selectedModel="gpt-5-nano"
      customModel=""
      onDraftChange={() => {}}
      onSend={() => {}}
      onTogglePipeline={() => {}}
      onModelChange={() => {}}
      onCustomModelChange={() => {}}
      {...overrides}
    />,
  );
}

test("shows only GPT-5 Nano and custom model options", () => {
  renderComposer();

  const options = screen.getAllByRole("option");
  expect(options).toHaveLength(2);
  expect(options[0]).toHaveTextContent("GPT-5 Nano");
  expect(options[0]).toHaveValue("gpt-5-nano");
  expect(options[1]).toHaveTextContent("Custom model");
  expect(options[1]).toHaveValue(CUSTOM_MODEL_VALUE);
  expect(screen.queryByRole("button", { name: "Add conclusion" })).not.toBeInTheDocument();
});

test("reveals the custom model input when custom model is selected", async () => {
  const user = userEvent.setup();
  const onModelChange = vi.fn();

  const { rerender } = renderComposer({ onModelChange });

  await user.selectOptions(screen.getByLabelText("LLM model"), CUSTOM_MODEL_VALUE);

  expect(onModelChange).toHaveBeenCalledWith(CUSTOM_MODEL_VALUE);

  rerender(
    <ChatComposer
      draft=""
      isTyping={false}
      runPipelineArmed={false}
      selectedModel={CUSTOM_MODEL_VALUE}
      customModel="openai/custom-model"
      onDraftChange={() => {}}
      onSend={() => {}}
      onTogglePipeline={() => {}}
      onModelChange={onModelChange}
      onCustomModelChange={() => {}}
    />,
  );

  expect(screen.getByLabelText("Custom model ID")).toHaveValue("openai/custom-model");
});
