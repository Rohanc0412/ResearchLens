import { createBrowserRouter, Navigate } from "react-router-dom";

import { ArtifactsPage } from "../../pages/artifacts/ArtifactsPage";
import { ConversationPage } from "../../pages/conversations/ConversationPage";
import { SnippetDetailPage } from "../../pages/evidence/SnippetDetailPage";
import { LoginPage } from "../../pages/login/LoginPage";
import { ProjectDetailPage } from "../../pages/projects/ProjectDetailPage";
import { ProjectsPage } from "../../pages/projects/ProjectsPage";
import { SecurityPage } from "../../pages/security/SecurityPage";
import { AppLayout } from "../layouts/AppLayout";
import { ProtectedRoute } from "./ProtectedRoute";
import { RouteErrorView } from "./RouteErrorView";

export const appRouter = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
    errorElement: <RouteErrorView />,
  },
  {
    element: <ProtectedRoute />,
    errorElement: <RouteErrorView />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate replace to="/projects" /> },
          { path: "/projects", element: <ProjectsPage /> },
          { path: "/projects/:projectId", element: <ProjectDetailPage /> },
          {
            path: "/projects/:projectId/conversations/:conversationId",
            element: <ConversationPage />,
          },
          { path: "/runs/:runId/artifacts", element: <ArtifactsPage /> },
          { path: "/evidence/snippets/:snippetId", element: <SnippetDetailPage /> },
          { path: "/security", element: <SecurityPage /> },
        ],
      },
    ],
  },
]);
