import { render, screen } from "@testing-library/react";

import { AppShell } from "./AppShell";


test("renders the phase 0 placeholder shell", () => {
  render(<AppShell />);
  expect(screen.getByText("ResearchLens Phase 0")).toBeInTheDocument();
});

