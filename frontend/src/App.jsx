import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import LoadingState from "./components/common/LoadingState";
import { apiService } from "./services/api";

const AppShell = lazy(() => import("./components/layout/AppShell"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const SignupPage = lazy(() => import("./pages/SignupPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const ActionQueuePage = lazy(() => import("./pages/ActionQueuePage"));
const GraphVisualizationPage = lazy(() => import("./pages/GraphVisualizationPage"));
const UserRiskProfilePage = lazy(() => import("./pages/UserRiskProfilePage"));
const CompliancePage = lazy(() => import("./pages/CompliancePage"));

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("cmds_auth_token");
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Suspense fallback={<div className="p-4 md:p-6"><LoadingState label="Loading page..." /></div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="action-queue" element={<ActionQueuePage />} />
          <Route path="graph" element={<GraphVisualizationPage />} />
          <Route path="compliance" element={<CompliancePage />} />
          <Route path="users/:userId" element={<UserRiskProfilePage />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}
