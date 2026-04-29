export type ReportSectionContent = {
  text: string;
  citations?: number[];
  isBullet?: boolean;
};

export type ReportSection = {
  id: string;
  heading: string;
  content: ReportSectionContent[];
};

export type ReportDocument = {
  title: string;
  sections: ReportSection[];
};

export const EMPTY_REPORT: ReportDocument = {
  title: "Research report",
  sections: [],
};
