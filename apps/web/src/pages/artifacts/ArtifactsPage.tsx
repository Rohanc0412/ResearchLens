import { ChevronLeft } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { Page } from "../../shared/ui/Page";
import { RunArtifactsWorkspace } from "../../widgets/artifacts_workspace/RunArtifactsWorkspace";

export function ArtifactsPage() {
  const { runId = "" } = useParams();
  const navigate = useNavigate();

  function handleBack() {
    if (window.history.length > 1) {
      navigate(-1);
      return;
    }

    navigate("/projects");
  }

  return (
    <Page
      eyebrow="Artifacts"
      title="Artifacts"
      subtitle={`Run ${runId}`}
      actions={
        <Button variant="ghost" compact onClick={handleBack}>
          <ChevronLeft size={16} />
          Back
        </Button>
      }
    >
      <RunArtifactsWorkspace runId={runId} />
    </Page>
  );
}
