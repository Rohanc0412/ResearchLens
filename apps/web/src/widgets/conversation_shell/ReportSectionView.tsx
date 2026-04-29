import { useEffect, useState } from "react";

import type { ReportSection } from "./reportDocument";

type ReportSectionViewProps = {
  section: ReportSection;
  onSave: (sectionId: string, content: string) => void;
};

export function ReportSectionView({ section, onSave }: ReportSectionViewProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    setDraft(section.content.map((item) => item.text).join("\n\n"));
  }, [section]);

  function handleSave() {
    onSave(section.id, draft);
    setEditing(false);
  }

  return (
    <section className="legacy-report-section">
      <div className="legacy-report-section__header">
        <h3 className="legacy-report-section__title">{section.heading}</h3>
        {!editing ? (
          <button onClick={() => setEditing(true)} className="legacy-report-section__action">
            Edit
          </button>
        ) : null}
      </div>

      {editing ? (
        <div className="legacy-report-section__editor">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            className="legacy-report-section__textarea"
          />
          <div className="legacy-report-section__editor-actions">
            <button
              onClick={() => {
                setDraft(section.content.map((item) => item.text).join("\n\n"));
                setEditing(false);
              }}
              className="legacy-report-section__button legacy-report-section__button--secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="legacy-report-section__button legacy-report-section__button--primary"
            >
              Save
            </button>
          </div>
        </div>
      ) : (
        <div className="legacy-report-section__content">
          {section.content.map((item, index) => (
            <div
              key={`${section.id}:${index}`}
              className={`legacy-report-section__row ${
                item.isBullet ? "legacy-report-section__row--bullet" : ""
              }`}
            >
              {item.isBullet ? (
                <span className="legacy-report-section__marker" aria-hidden="true">
                  *
                </span>
              ) : null}
              <p className="legacy-report-section__text">
                <span>{item.text}</span>
                {item.citations?.length ? (
                  <span className="legacy-report-section__citations">
                    {item.citations.map((citation) => `[${citation}]`).join("")}
                  </span>
                ) : null}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
