import { useState } from "react";

import { usePostMessageMutation } from "../../entities/message/message.api";
import { getErrorMessage } from "../../shared/api/errors";
import { titleFromPrompt } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Textarea } from "../../shared/ui/Textarea";

export function ConversationComposer({
  conversationId,
  onResearch,
}: {
  conversationId: string;
  onResearch: (payload: { text: string; sourceMessageId: string }) => Promise<void>;
}) {
  const postMessage = usePostMessageMutation(conversationId);
  const [text, setText] = useState("");
  const [modeError, setModeError] = useState<string | null>(null);

  const saveMessage = async (startRun: boolean) => {
    try {
      setModeError(null);
      const message = await postMessage.mutateAsync({
        role: "user",
        type: "text",
        content_text: text,
        client_message_id: crypto.randomUUID(),
      });
      const prompt = text;
      setText("");
      if (startRun) {
        await onResearch({ text: prompt, sourceMessageId: message.id });
      }
    } catch (error) {
      setModeError(getErrorMessage(error));
    }
  };

  return (
    <div className="stack">
      {modeError ? <ErrorBanner body={modeError} /> : null}
      <Textarea
        label="Prompt"
        hint={`Title preview: ${titleFromPrompt(text || "Untitled conversation")}`}
        value={text}
        rows={5}
        onChange={(event) => setText(event.target.value)}
      />
      <div className="row">
        <Button
          variant="secondary"
          loading={postMessage.isPending}
          disabled={!text.trim()}
          onClick={() => void saveMessage(false)}
        >
          Save message
        </Button>
        <Button
          variant="primary"
          loading={postMessage.isPending}
          disabled={!text.trim()}
          onClick={() => void saveMessage(true)}
        >
          Research
        </Button>
      </div>
    </div>
  );
}
