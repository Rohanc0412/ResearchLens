import { EMPTY_REPORT, type ReportDocument, type ReportSection } from "./reportDocument";

function generateId() {
  return `report-section:${crypto.randomUUID()}`;
}

function extractInlineCitations(input: string): { text: string; citations: number[] } {
  const citations: number[] = [];
  const citationPattern = /\[(\d+)\]|\[\^(\d+)\]/g;
  const text = input.replace(citationPattern, (_match, first, second) => {
    const raw = first ?? second;
    const value = Number(raw);
    if (!Number.isNaN(value)) citations.push(value);
    return "";
  });

  const normalized = text
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:!?])/g, "$1")
    .trim();

  return {
    text: normalized,
    citations: Array.from(new Set(citations)),
  };
}

function isReferencesHeading(line: string) {
  const normalized = line.trim().toLowerCase();
  return (
    normalized === "## references" ||
    normalized === "## reference" ||
    normalized === "## bibliography" ||
    normalized === "## citations"
  );
}

export function extractReportTitle(markdown: string): string | null {
  for (const line of markdown.replace(/\r\n/g, "\n").split("\n")) {
    const match = line.match(/^#\s+(.+)$/);
    if (match?.[1]?.trim()) return match[1].trim();
  }
  return null;
}

export function parseReportMarkdown(markdown: string, fallbackTitle?: string): ReportDocument {
  const normalized = markdown.replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return {
      ...EMPTY_REPORT,
      title: fallbackTitle?.trim() || EMPTY_REPORT.title,
    };
  }

  const sections: ReportSection[] = [];
  const lines = normalized.split("\n");
  const title = extractReportTitle(normalized) ?? fallbackTitle?.trim() ?? EMPTY_REPORT.title;

  let currentSection: ReportSection | null = null;
  let paragraphBuffer: string[] = [];
  let lastFootnoteIndex: number | null = null;

  const ensureSection = (heading: string) => {
    if (!currentSection) {
      currentSection = {
        id: generateId(),
        heading,
        content: [],
      };
    }
  };

  const pushCurrentSection = () => {
    if (currentSection && currentSection.content.length > 0) {
      sections.push(currentSection);
    }
    currentSection = null;
  };

  const flushParagraph = () => {
    if (!currentSection || paragraphBuffer.length === 0) return;
    const rawText = paragraphBuffer.join(" ").trim();
    paragraphBuffer = [];
    lastFootnoteIndex = null;
    if (!rawText) return;

    const extracted = extractInlineCitations(rawText);
    currentSection.content.push({
      text: extracted.text || rawText,
      citations: extracted.citations.length > 0 ? extracted.citations : undefined,
      isBullet: false,
    });
  };

  const pushBullet = (raw: string) => {
    ensureSection("Live Report");
    flushParagraph();

    const extracted = extractInlineCitations(raw);
    currentSection?.content.push({
      text: extracted.text || raw,
      citations: extracted.citations.length > 0 ? extracted.citations : undefined,
      isBullet: true,
    });
    lastFootnoteIndex = null;
  };

  const pushReferenceFootnote = (num: number, content: string) => {
    ensureSection("References");
    flushParagraph();
    currentSection?.content.push({
      text: `[${num}] ${content}`.trim(),
      isBullet: true,
    });
    lastFootnoteIndex = (currentSection?.content.length ?? 1) - 1;
  };

  for (const line of lines) {
    const headingMatch = line.match(/^(#{2,3})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      pushCurrentSection();
      currentSection = {
        id: generateId(),
        heading: headingMatch[2].trim(),
        content: [],
      };
      lastFootnoteIndex = null;
      continue;
    }

    if (/^#\s+/.test(line)) continue;

    if (isReferencesHeading(line) || line.trim() === "---") {
      flushParagraph();
      pushCurrentSection();
      currentSection = {
        id: generateId(),
        heading: "References",
        content: [],
      };
      lastFootnoteIndex = null;
      continue;
    }

    if (line.trim() === "") {
      flushParagraph();
      continue;
    }

    const footnoteMatch = line.match(/^\[\^(\d+)\]:\s*(.*)$/);
    if (footnoteMatch) {
      pushReferenceFootnote(Number(footnoteMatch[1]), footnoteMatch[2] ?? "");
      continue;
    }

    if (lastFootnoteIndex !== null && /^\s{2,}\S+/.test(line)) {
      const currentItem = currentSection?.content[lastFootnoteIndex];
      if (currentItem) currentItem.text = `${currentItem.text} ${line.trim()}`.trim();
      continue;
    }

    const bulletMatch = line.match(/^\s*[-*+]\s+(.*)$/);
    if (bulletMatch) {
      pushBullet(bulletMatch[1] ?? "");
      continue;
    }

    const numberedMatch = line.match(/^\s*\d+\.\s+(.*)$/);
    if (numberedMatch) {
      pushBullet(numberedMatch[1] ?? "");
      continue;
    }

    ensureSection("Live Report");
    paragraphBuffer.push(line.trim());
  }

  flushParagraph();
  pushCurrentSection();

  return {
    title,
    sections,
  };
}
