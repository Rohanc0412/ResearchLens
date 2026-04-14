import { useParams } from "react-router-dom";

import {
  useChunkDetailQuery,
  useSourceDetailQuery,
} from "../../entities/evidence/evidence.api";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { Page } from "../../shared/ui/Page";

export function SnippetDetailPage() {
  const { snippetId = "" } = useParams();
  const chunk = useChunkDetailQuery(snippetId);
  const source = useSourceDetailQuery(chunk.data?.source_id ?? "");

  if (!chunk.isLoading && !chunk.data) {
    return (
      <Page eyebrow="Evidence" title="Snippet not found">
        <EmptyState
          title="Snippet not found"
          body="The requested evidence snippet was not available for the current tenant."
        />
      </Page>
    );
  }

  return (
    <Page
      eyebrow="Evidence"
      title={chunk.data?.source_title ?? "Snippet detail"}
      subtitle="Durable retrieval chunk with source metadata and surrounding context."
    >
      <div className="evidence-workbench">
        <Card className="preview-panel" title="Snippet text" meta={`Chunk ${chunk.data?.chunk_index ?? 0}`}>
          <div className="stack">
            <p>{chunk.data?.chunk_text}</p>
            {(chunk.data?.context_chunks ?? []).map((item) => (
              <div key={item.chunk_id} className="evidence-chunk">
                  <div className="meta-line">Context chunk {item.chunk_index}</div>
                  <div>{item.excerpt_text}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="workspace-panel" title="Source metadata" meta={source.data?.canonical_key ?? "Loading"}>
          <div className="stack">
            <div className="meta-line">
              {source.data?.authors.join(", ") || "Author metadata unavailable"}
            </div>
            <div>{source.data?.venue ?? "Venue unavailable"}</div>
            <div>{source.data?.year ?? "Year unavailable"}</div>
            <div className="meta-line">
              {JSON.stringify(source.data?.identifiers ?? {}, null, 2)}
            </div>
            {source.data?.url ? (
              <a href={source.data.url} rel="noreferrer" target="_blank">
                <span className="pill">Open source</span>
              </a>
            ) : null}
          </div>
        </Card>
      </div>
    </Page>
  );
}
