import { useState } from "react";

import { useCreateProjectMutation } from "../../entities/project/project.api";
import { getErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Input } from "../../shared/ui/Input";
import { Textarea } from "../../shared/ui/Textarea";

export function CreateProjectDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const createProject = useCreateProjectMutation();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const submit = async () => {
    await createProject.mutateAsync({
      name,
      description: description || undefined,
    });
    setName("");
    setDescription("");
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="New Project"
    >
      <div className="stack">
        {createProject.error ? (
          <ErrorBanner body={getErrorMessage(createProject.error)} />
        ) : null}
        <Input
          label="Name"
          placeholder="e.g. Market landscape: LLM evaluation"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <Textarea
          label="Description (optional)"
          placeholder="What is this project about?"
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <div className="row row--between">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={createProject.isPending}
            onClick={() => void submit()}
            disabled={!name.trim()}
          >
            Create project
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
