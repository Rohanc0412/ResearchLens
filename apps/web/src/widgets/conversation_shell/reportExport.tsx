import { pdf, Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";
import { Document as WordDocument, HeadingLevel, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

import type { ReportDocument, ReportSection } from "./reportDocument";

const pdfStyles = StyleSheet.create({
  page: {
    paddingTop: 28,
    paddingBottom: 36,
    paddingHorizontal: 34,
    backgroundColor: "#ffffff",
    fontFamily: "Helvetica",
  },
  title: {
    fontSize: 20,
    color: "#111827",
    marginBottom: 16,
    fontFamily: "Helvetica-Bold",
  },
  section: {
    marginBottom: 14,
  },
  sectionHeading: {
    fontSize: 13,
    color: "#111827",
    marginBottom: 6,
    fontFamily: "Helvetica-Bold",
  },
  paragraph: {
    fontSize: 10.5,
    color: "#1f2937",
    lineHeight: 1.5,
    marginBottom: 4,
  },
  bulletRow: {
    flexDirection: "row",
    marginBottom: 4,
  },
  bulletMarker: {
    width: 12,
    fontSize: 10.5,
    color: "#2563eb",
  },
  bulletText: {
    flex: 1,
    fontSize: 10.5,
    color: "#1f2937",
    lineHeight: 1.5,
  },
  citation: {
    color: "#2563eb",
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
  },
});

type ReportExportFormat = "pdf" | "docx" | "md" | "html";

function appendCitations(text: string, citations?: number[]) {
  if (!citations || citations.length === 0) return text;
  return `${text}${citations.map((citation) => `[${citation}]`).join("")}`;
}

function buildMarkdown(report: ReportDocument) {
  const lines = [`# ${report.title}`, ""];
  for (const section of report.sections) {
    lines.push(`## ${section.heading}`, "");
    for (const item of section.content) {
      const prefix = item.isBullet ? "- " : "";
      lines.push(`${prefix}${appendCitations(item.text, item.citations)}`, "");
    }
  }
  return `${lines.join("\n").trim()}\n`;
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function buildHtml(report: ReportDocument) {
  const sections = report.sections
    .map((section) => {
      const content = section.content
        .map((item) => {
          const body = escapeHtml(item.text);
          const citations =
            item.citations && item.citations.length > 0
              ? `<span class="report-export__citations">${item.citations
                  .map((citation) => `[${citation}]`)
                  .join("")}</span>`
              : "";
          if (item.isBullet) return `<p class="report-export__bullet">* ${body}${citations}</p>`;
          return `<p>${body}${citations}</p>`;
        })
        .join("\n");
      return `<section><h2>${escapeHtml(section.heading)}</h2>${content}</section>`;
    })
    .join("\n");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(report.title)}</title>
  <style>
    body { font-family: Georgia, serif; color: #111827; margin: 0; background: #f8fafc; }
    main { max-width: 860px; margin: 0 auto; padding: 40px 28px 72px; background: #ffffff; }
    h1 { font-size: 2rem; margin: 0 0 1.5rem; }
    h2 { font-size: 1.25rem; margin: 1.5rem 0 0.75rem; }
    p { line-height: 1.7; font-size: 1rem; color: #1f2937; }
    .report-export__bullet { padding-left: 1.25rem; text-indent: -1.25rem; }
    .report-export__citations { color: #2563eb; font-size: 0.85em; margin-left: 0.15rem; }
  </style>
</head>
<body>
  <main>
    <h1>${escapeHtml(report.title)}</h1>
    ${sections}
  </main>
</body>
</html>`;
}

function downloadText(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  saveAs(blob, filename);
}

function ReportPdf({ report }: { report: ReportDocument }) {
  return (
    <Document>
      <Page size="A4" style={pdfStyles.page}>
        <Text style={pdfStyles.title}>{report.title}</Text>
        {report.sections.map((section) => (
          <PdfSection key={section.id} section={section} />
        ))}
      </Page>
    </Document>
  );
}

function PdfSection({ section }: { section: ReportSection }) {
  return (
    <View style={pdfStyles.section}>
      <Text style={pdfStyles.sectionHeading}>{section.heading}</Text>
      {section.content.map((item, index) =>
        item.isBullet ? (
          <View key={`${section.id}:${index}`} style={pdfStyles.bulletRow}>
            <Text style={pdfStyles.bulletMarker}>*</Text>
            <PdfText text={item.text} citations={item.citations} bullet />
          </View>
        ) : (
          <PdfText
            key={`${section.id}:${index}`}
            text={item.text}
            citations={item.citations}
          />
        ),
      )}
    </View>
  );
}

function PdfText({
  text,
  citations,
  bullet = false,
}: {
  text: string;
  citations?: number[];
  bullet?: boolean;
}) {
  return (
    <Text style={bullet ? pdfStyles.bulletText : pdfStyles.paragraph}>
      {text}
      {citations && citations.length > 0 ? (
        <Text style={pdfStyles.citation}>{citations.map((value) => `[${value}]`).join("")}</Text>
      ) : null}
    </Text>
  );
}

async function buildDocx(report: ReportDocument) {
  const children: Paragraph[] = [
    new Paragraph({
      text: report.title,
      heading: HeadingLevel.HEADING_1,
      spacing: { after: 240 },
    }),
  ];

  for (const section of report.sections) {
    children.push(
      new Paragraph({
        text: section.heading,
        heading: HeadingLevel.HEADING_2,
        spacing: { before: 200, after: 120 },
      }),
    );

    for (const item of section.content) {
      const runs: TextRun[] = [new TextRun(item.text)];
      if (item.citations?.length) {
        runs.push(
          new TextRun({
            text: ` ${item.citations.map((citation) => `[${citation}]`).join("")}`,
            superScript: true,
            color: "2563EB",
          }),
        );
      }
      children.push(
        new Paragraph({
          children: runs,
          bullet: item.isBullet ? { level: 0 } : undefined,
          spacing: { after: 120 },
        }),
      );
    }
  }

  const document = new WordDocument({
    sections: [{ properties: {}, children }],
  });

  return Packer.toBlob(document);
}

function sanitizeFilename(value: string) {
  return value.replace(/[<>:"/\\|?*\u0000-\u001f]/g, "").trim() || "research-report";
}

export async function exportReport(report: ReportDocument, format: ReportExportFormat) {
  const filename = sanitizeFilename(report.title);
  if (format === "md") {
    downloadText(buildMarkdown(report), `${filename}.md`, "text/markdown;charset=utf-8");
    return;
  }
  if (format === "html") {
    downloadText(buildHtml(report), `${filename}.html`, "text/html;charset=utf-8");
    return;
  }
  if (format === "docx") {
    const blob = await buildDocx(report);
    saveAs(blob, `${filename}.docx`);
    return;
  }

  const blob = await pdf(<ReportPdf report={report} />).toBlob();
  saveAs(blob, `${filename}.pdf`);
}
