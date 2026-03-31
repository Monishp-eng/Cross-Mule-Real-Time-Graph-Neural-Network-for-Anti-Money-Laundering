import { createBrowserRouter } from "react-router";
import { RootLayout } from "./components/RootLayout";
import { DashboardView } from "./components/DashboardView";
import { GraphView } from "./components/GraphView";
import { AlertsView } from "./components/AlertsView";
import { TransactionsView } from "./components/TransactionsView";
import { ReportsView } from "./components/ReportsView";
import { SettingsView } from "./components/SettingsView";
import { LoginPage } from "./components/auth/LoginPage";
import { SignupPage } from "./components/auth/SignupPage";
import { RiskScoringView } from "./components/RiskScoringView";
import { ChannelFlowView } from "./components/ChannelFlowView";

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: LoginPage,
  },
  {
    path: "/signup",
    Component: SignupPage,
  },
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, Component: DashboardView },
      { path: "graph", Component: GraphView },
      { path: "alerts", Component: AlertsView },
      { path: "risk-scoring", Component: RiskScoringView },
      { path: "channel-flow", Component: ChannelFlowView },
      { path: "transactions", Component: TransactionsView },
      { path: "reports", Component: ReportsView },
      { path: "settings", Component: SettingsView },
    ],
  },
]);