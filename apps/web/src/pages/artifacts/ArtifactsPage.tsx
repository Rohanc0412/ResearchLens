import { useSearchParams, useParams } from "react-router-dom";

import { Page } from "../../shared/ui/Page";
import { ArtifactBrowser } from "../../widgets/artifact_list/ArtifactBrowser";
import { EvidenceOverview } from "../../widgets/evidence_panel/EvidenceOverview";

export function ArtifactsPage() {
  const { runId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const sectionId = searchParams.get("section");

  return (
    <Page
      eyebrow="Artifacts"
      title="Run outputs"
      subtitle="Artifacts, previewable exports, evaluation summary, and evidence linkage."
    >
      <div className="inspection-shell">
        <ArtifactBrowser runId={runId} />
      </div>
      <div id="evidence">
        <EvidenceOverview runId={runId} sectionId={sectionId} />
      </div>
    </Page>
  );
}
