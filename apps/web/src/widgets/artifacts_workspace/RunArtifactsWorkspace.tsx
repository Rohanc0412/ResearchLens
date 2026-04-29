import type {
  ArtifactResponse,
  EvaluationIssueResponse,
  RepairSectionResponse,
} from "@researchlens/api-client";
import {
  BarChart3,
  Download,
  Eye,
  FileJson2,
  FileText,
  FlaskConical,
} from "lucide-react";
import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Link, useSearchParams } from "react-router-dom";
import remarkGfm from "remark-gfm";

import {
  useArtifactDownloadMutation,
  useArtifactsQuery,
  useArtifactTextQuery,
} from "../../entities/artifact/artifact.api";
import {
  useEvaluationIssuesQuery,
  useEvaluationSummaryQuery,
  useRepairSummaryQuery,
  useRunEvidenceSummaryQuery,
  useSectionEvidenceQuery,
} from "../../entities/evidence/evidence.api";
import { useRunQuery } from "../../entities/run/run.api";
import { formatDateTime } from "../../shared/lib/format";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { saveBlob } from "../conversation_shell/reportPane.download";

type WorkspaceTab = "artifacts" | "evidence" | "evaluation";

const TABS: Array<{ id: WorkspaceTab; label: string; icon: typeof FileText }> = [
  { id: "artifacts", label: "Artifacts", icon: FileText },
  { id: "evidence", label: "Evidence", icon: FlaskConical },
  { id: "evaluation", label: "Evaluation", icon: BarChart3 },
];

function getWorkspaceTab(value: string | null): WorkspaceTab {
  return value === "evidence" || value === "evaluation" ? value : "artifacts";
}

function isInlinePreviewable(artifact: ArtifactResponse) {
  const mediaType = artifact.media_type.toLowerCase();
  const filename = artifact.filename.toLowerCase();

  return (
    mediaType.startsWith("text/") ||
    mediaType.includes("json") ||
    mediaType.includes("markdown") ||
    filename.endsWith(".md") ||
    filename.endsWith(".markdown") ||
    filename.endsWith(".txt") ||
    filename.endsWith(".json")
  );
}

function isMarkdownArtifact(artifact: ArtifactResponse, mediaType?: string) {
  const currentMediaType = (mediaType ?? artifact.media_type).toLowerCase();
  const filename = artifact.filename.toLowerCase();

  return (
    currentMediaType.includes("markdown") ||
    filename.endsWith(".md") ||
    filename.endsWith(".markdown")
  );
}

function formatBytes(value: number) {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 1,
    notation: value >= 1024 ? "compact" : "standard",
  }).format(value) + " bytes";
}

function getArtifactGlyph(artifact: ArtifactResponse) {
  return artifact.media_type.includes("json") ? <FileJson2 size={15} /> : <FileText size={15} />;
}

function MetricCard({
  label,
  value,
  meta,
}: {
  label: string;
  value: string;
  meta: string;
}) {
  return (
    <div className="artifacts-evaluation__metric">
      <span className="artifacts-evaluation__metric-value">{value}</span>
      <strong>{label}</strong>
      <span className="meta-line">{meta}</span>
    </div>
  );
}

function IssueCard({ issue }: { issue: EvaluationIssueResponse }) {
  return (
    <article className="event-log__item stack">
      <div className="row row--between">
        <strong>{issue.message}</strong>
        <span className="pill">{issue.severity}</span>
      </div>
      <div className="meta-line">
        {issue.section_title} | {issue.issue_type} | {formatDateTime(issue.created_at)}
      </div>
      <div>{issue.rationale}</div>
      {issue.repair_hint ? <div className="meta-line">Repair hint: {issue.repair_hint}</div> : null}
    </article>
  );
}

function RepairSectionCard({ item }: { item: RepairSectionResponse }) {
  return (
    <article className="section-row">
      <div className="stack">
        <strong>{item.section_title}</strong>
        <div className="meta-line">
          {item.status} | {item.action} | {item.changed ? "Changed" : "Unchanged"}
        </div>
        {item.unresolved_reason ? <div>{item.unresolved_reason}</div> : null}
      </div>
      <span className="pill">{item.section_order + 1}</span>
    </article>
  );
}

export function RunArtifactsWorkspace({ runId }: { runId: string }) {
  const [searchParams, setSearchParams] = useSearchParams();

  const run = useRunQuery(runId);
  const artifacts = useArtifactsQuery(runId);
  const evidence = useRunEvidenceSummaryQuery(runId);
  const evaluationReady =
    run.data?.current_stage === "repair" ||
    run.data?.current_stage === "export" ||
    run.data?.status === "succeeded";
  const evaluation = useEvaluationSummaryQuery(runId, { enabled: evaluationReady });
  const issues = useEvaluationIssuesQuery(runId);
  const repair = useRepairSummaryQuery(runId);
  const download = useArtifactDownloadMutation();

  const activeTab = getWorkspaceTab(searchParams.get("tab"));
  const focusId = searchParams.get("focus");
  const sectionId = searchParams.get("section");

  const selectedArtifact = useMemo(
    () => (artifacts.data ?? []).find((artifact) => artifact.id === focusId) ?? null,
    [artifacts.data, focusId],
  );
  const previewArtifact =
    selectedArtifact && isInlinePreviewable(selectedArtifact) ? selectedArtifact : null;
  const preview = useArtifactTextQuery(previewArtifact?.id ?? "", previewArtifact?.filename, {
    enabled: Boolean(previewArtifact),
  });
  const selectedSection = useSectionEvidenceQuery(runId, sectionId ?? "");

  function updateWorkspaceState(
    updates: Partial<Record<"tab" | "focus" | "section", string | null>>,
  ) {
    const next = new URLSearchParams(searchParams);

    for (const [key, value] of Object.entries(updates)) {
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
    }

    setSearchParams(next);
  }

  async function handleArtifactDownload(artifact: ArtifactResponse) {
    const result = await download.mutateAsync(artifact);
    saveBlob(result.blob, result.filename);
  }

  return (
    <section className="artifacts-workspace stack">
      <div className="artifacts-workspace__header">
        <div className="artifacts-workspace__run-meta">
          <span className="pill">{run.data?.display_status ?? "Loading status"}</span>
          <span className="meta-line">
            {run.data?.display_stage ? `${run.data.display_stage} | ` : ""}
            Updated {formatDateTime(run.data?.updated_at)}
          </span>
        </div>
        <div className="artifacts-tabs" role="tablist" aria-label="Run artifact workspace tabs">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={activeTab === id}
              className="artifacts-tabs__tab"
              data-active={activeTab === id}
              onClick={() => updateWorkspaceState({ tab: id })}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "artifacts" ? (
        <div className="artifacts-pane-grid">
          <Card
            className="workspace-panel"
            title="Artifact library"
            meta={
              artifacts.data ? `${artifacts.data.length} files` : artifacts.isLoading ? "Loading" : ""
            }
          >
            {artifacts.error ? <ErrorBanner body="Artifacts could not be loaded." /> : null}
            {artifacts.isLoading ? <div className="meta-line">Loading artifacts...</div> : null}
            {!artifacts.isLoading && !artifacts.error && (artifacts.data?.length ?? 0) === 0 ? (
              <EmptyState
                title="No artifacts yet"
                body="Artifacts will appear here once this run completes."
              />
            ) : null}
            {(artifacts.data?.length ?? 0) > 0 ? (
              <div className="artifacts-list">
                {(artifacts.data ?? []).map((artifact) => {
                  const previewable = isInlinePreviewable(artifact);
                  const selected = selectedArtifact?.id === artifact.id;

                  return (
                    <article
                      key={artifact.id}
                      className="artifacts-list__item"
                      data-selected={selected}
                    >
                      <button
                        type="button"
                        className="artifacts-list__select"
                        onClick={() =>
                          updateWorkspaceState({
                            tab: "artifacts",
                            focus: artifact.id,
                          })
                        }
                      >
                        <span className="artifacts-list__glyph">{getArtifactGlyph(artifact)}</span>
                        <span className="artifacts-list__body">
                          <span className="artifacts-list__badges">
                            <span className="pill">{artifact.kind}</span>
                          </span>
                          <strong>{artifact.filename}</strong>
                          <span className="meta-line">
                            {formatDateTime(artifact.created_at)} | {formatBytes(artifact.byte_size)}
                          </span>
                          <span className="meta-line">{artifact.media_type}</span>
                        </span>
                      </button>
                      <div className="artifacts-list__actions">
                        <Button
                          compact
                          variant="ghost"
                          aria-label={`Download ${artifact.filename}`}
                          onClick={() => void handleArtifactDownload(artifact)}
                        >
                          <Download size={15} />
                        </Button>
                        {previewable ? (
                          <Button
                            compact
                            variant="ghost"
                            aria-label={`Preview ${artifact.filename}`}
                            onClick={() =>
                              updateWorkspaceState({
                                tab: "artifacts",
                                focus: artifact.id,
                              })
                            }
                          >
                            <Eye size={15} />
                          </Button>
                        ) : null}
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : null}
          </Card>

          <Card
            className="preview-panel"
            title={selectedArtifact?.filename ?? "Preview"}
            meta={
              selectedArtifact
                ? `${selectedArtifact.kind} | ${selectedArtifact.media_type}`
                : "Select an artifact to inspect"
            }
          >
            {!selectedArtifact ? (
              <div className="artifacts-preview__placeholder">
                Select an artifact to preview it inline or download it.
              </div>
            ) : !previewArtifact ? (
              <div className="artifacts-preview__placeholder">
                This artifact is available for download only.
              </div>
            ) : preview.error ? (
              <ErrorBanner body="The selected artifact could not be previewed." />
            ) : preview.isLoading ? (
              <div className="meta-line">Loading preview...</div>
            ) : preview.data ? (
              isMarkdownArtifact(previewArtifact, preview.data.mediaType) ? (
                <div className="artifacts-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {preview.data.text}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="preview">
                  <pre>{preview.data.text}</pre>
                </div>
              )
            ) : (
              <div className="artifacts-preview__placeholder">
                Preview content is not available for this artifact.
              </div>
            )}
          </Card>
        </div>
      ) : null}

      {activeTab === "evidence" ? (
        <div className="artifacts-pane-grid">
          <Card
            className="workspace-panel"
            title="Sections"
            meta={
              evidence.data
                ? `${evidence.data.section_count} sections | ${evidence.data.chunk_count} snippets`
                : evidence.isLoading
                  ? "Loading"
                  : ""
            }
          >
            {evidence.error ? <ErrorBanner body="Evidence summary could not be loaded." /> : null}
            {evidence.isLoading ? <div className="meta-line">Loading evidence...</div> : null}
            {!evidence.isLoading && !evidence.error && !evidence.data ? (
              <EmptyState
                title="No evidence available"
                body="This run does not expose persisted evidence yet."
              />
            ) : null}
            {evidence.data ? (
              <div className="artifacts-list">
                {evidence.data.sections.map((item) => (
                  <article
                    key={item.section_id}
                    className="artifacts-list__item"
                    data-selected={sectionId === item.section_id}
                  >
                    <button
                      type="button"
                      className="artifacts-list__select"
                      onClick={() =>
                        updateWorkspaceState({
                          tab: "evidence",
                          section: item.section_id,
                        })
                      }
                    >
                      <span className="artifacts-list__glyph">
                        <FlaskConical size={15} />
                      </span>
                      <span className="artifacts-list__body">
                        <strong>{item.title}</strong>
                        <span className="meta-line">
                          Section {item.section_order + 1} | {item.issue_count} issues
                        </span>
                        <span className="meta-line">
                          {item.repaired ? "Repaired canonical text" : "Draft canonical text"}
                        </span>
                      </span>
                    </button>
                  </article>
                ))}
              </div>
            ) : null}
          </Card>

          <Card
            className="preview-panel"
            title={selectedSection.data?.section_title ?? "Section trace"}
            meta={sectionId ?? "Choose a section"}
          >
            {selectedSection.error ? (
              <ErrorBanner body="Section trace could not be loaded." />
            ) : null}
            {!sectionId ? (
              <div className="artifacts-preview__placeholder">
                Choose a section to inspect its claim and source trace.
              </div>
            ) : selectedSection.isLoading ? (
              <div className="meta-line">Loading section trace...</div>
            ) : !selectedSection.data ? (
              <div className="artifacts-preview__placeholder">
                Section trace is not available for this run yet.
              </div>
            ) : (
              <div className="stack">
                <section className="artifacts-detail-card">
                  <div className="eyebrow">Canonical Summary</div>
                  <p>{selectedSection.data.canonical_summary}</p>
                </section>

                {selectedSection.data.unresolved_quality_findings.length > 0 ? (
                  <section className="stack">
                    <div className="eyebrow">Unresolved Findings</div>
                    {selectedSection.data.unresolved_quality_findings.map((item) => (
                      <article key={item.issue_id} className="event-log__item stack">
                        <div className="row row--between">
                          <strong>{item.message}</strong>
                          <span className="pill">{item.severity}</span>
                        </div>
                        <div>{item.rationale}</div>
                        {item.repair_hint ? (
                          <div className="meta-line">Repair hint: {item.repair_hint}</div>
                        ) : null}
                      </article>
                    ))}
                  </section>
                ) : null}

                {selectedSection.data.issues.length > 0 ? (
                  <section className="stack">
                    <div className="eyebrow">Evaluation Issues</div>
                    {selectedSection.data.issues.map((item) => (
                      <article key={item.issue_id} className="event-log__item stack">
                        <div className="row row--between">
                          <strong>{item.message}</strong>
                          <span className="pill">{item.severity}</span>
                        </div>
                        <div>{item.rationale}</div>
                      </article>
                    ))}
                  </section>
                ) : null}

                <section className="stack">
                  <div className="eyebrow">Evidence Chunks</div>
                  {selectedSection.data.evidence_chunks.length > 0 ? (
                    selectedSection.data.evidence_chunks.map((chunk) => (
                      <article key={chunk.chunk_id} className="evidence-chunk stack">
                        <div className="row row--between">
                          <strong>{chunk.source_title ?? "Untitled source"}</strong>
                          <span className="meta-line">Chunk {chunk.chunk_index}</span>
                        </div>
                        <div>{chunk.excerpt_text}</div>
                        <Link
                          className="artifacts-inline-link"
                          to={`/evidence/snippets/${chunk.chunk_id}`}
                        >
                          Open snippet
                        </Link>
                      </article>
                    ))
                  ) : (
                    <div className="meta-line">No persisted evidence chunks for this section.</div>
                  )}
                </section>

                {selectedSection.data.source_refs.length > 0 ? (
                  <section className="stack">
                    <div className="eyebrow">Sources</div>
                    {selectedSection.data.source_refs.map((source) => (
                      <article key={source.source_id} className="artifacts-source-row">
                        <div>
                          <strong>{source.title ?? "Untitled source"}</strong>
                          <div className="meta-line">
                            {source.canonical_key} | {source.source_id}
                          </div>
                        </div>
                        <span className="pill">Source ref</span>
                      </article>
                    ))}
                  </section>
                ) : null}
              </div>
            )}
          </Card>
        </div>
      ) : null}

      {activeTab === "evaluation" ? (
        <Card className="workspace-panel" title="Evaluation" meta="Read-only run quality summary">
          {evaluation.error ? <ErrorBanner body="Evaluation summary could not be loaded." /> : null}
          {repair.error ? <ErrorBanner body="Repair summary could not be loaded." /> : null}
          <div className="stack">
            {evaluation.isLoading ? <div className="meta-line">Loading evaluation...</div> : null}
            {!evaluation.isLoading && !evaluation.data && !repair.data ? (
              <EmptyState
                title="No evaluation summary yet"
                body="Evaluation results will appear here after the run reaches the evaluation stage."
              />
            ) : null}

            {evaluation.data ? (
              <>
                <div className="artifacts-evaluation__metrics">
                  <MetricCard
                    label="Quality"
                    value={`${evaluation.data.quality_pct.toFixed(1)}%`}
                    meta="overall score"
                  />
                  <MetricCard
                    label="Pass Rate"
                    value={`${evaluation.data.pass_rate.toFixed(1)}%`}
                    meta="supported claims"
                  />
                  <MetricCard
                    label="RAGAS"
                    value={`${evaluation.data.ragas_faithfulness_pct.toFixed(1)}%`}
                    meta="faithfulness"
                  />
                  <MetricCard
                    label="Repair"
                    value={String(evaluation.data.sections_requiring_repair_count)}
                    meta="sections requiring repair"
                  />
                </div>

                {evaluation.data.sections_requiring_repair.length > 0 ? (
                  <section className="stack">
                    <div className="eyebrow">Sections Requiring Repair</div>
                    <div className="artifacts-chip-list">
                      {evaluation.data.sections_requiring_repair.map((item) => (
                        <button
                          key={item}
                          type="button"
                          className="pill artifacts-chip-button"
                          onClick={() =>
                            updateWorkspaceState({
                              tab: "evidence",
                              section: item,
                            })
                          }
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </section>
                ) : null}
              </>
            ) : null}

            <section className="stack">
              <div className="eyebrow">Issues</div>
              {issues.isLoading ? <div className="meta-line">Loading issues...</div> : null}
              {!issues.isLoading && (issues.data?.length ?? 0) === 0 ? (
                <div className="meta-line">No evaluation issues recorded for this run.</div>
              ) : null}
              {(issues.data ?? []).map((issue) => (
                <IssueCard key={issue.issue_id} issue={issue} />
              ))}
            </section>

            <section className="stack">
              <div className="eyebrow">Repair Summary</div>
              {repair.data ? (
                <>
                  <div className="artifacts-evaluation__metrics">
                    <MetricCard
                      label="Selected"
                      value={String(repair.data.selected_count)}
                      meta={repair.data.status}
                    />
                    <MetricCard
                      label="Changed"
                      value={String(repair.data.changed_count)}
                      meta="sections updated"
                    />
                    <MetricCard
                      label="Unresolved"
                      value={String(repair.data.unresolved_count)}
                      meta="remaining issues"
                    />
                  </div>
                  {repair.data.sections.length > 0 ? (
                    <div className="stack">
                      {repair.data.sections.map((item) => (
                        <RepairSectionCard key={item.repair_result_id} item={item} />
                      ))}
                    </div>
                  ) : (
                    <div className="meta-line">No repair section records available.</div>
                  )}
                </>
              ) : (
                <div className="meta-line">No repair summary available for this run.</div>
              )}
            </section>
          </div>
        </Card>
      ) : null}
    </section>
  );
}
