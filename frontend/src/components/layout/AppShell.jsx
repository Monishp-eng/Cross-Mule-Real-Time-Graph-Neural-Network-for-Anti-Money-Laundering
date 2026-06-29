import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/action-queue", label: "Action Queue" },
  { to: "/graph", label: "Network Explorer" },
  { to: "/compliance", label: "Compliance Reports" },
];

export default function AppShell() {
  const navigate = useNavigate();
  const [theme, setTheme] = useState(localStorage.getItem("cmds_theme") || "dark");
  const authToken = localStorage.getItem("cmds_auth_token");
  const accountEmail = localStorage.getItem("cmds_auth_email") || "";
  const staffRole = localStorage.getItem("cmds_auth_role") || "ANALYST";
  const employeeId = localStorage.getItem("cmds_auth_employee_id") || "";

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("cmds_theme", theme);
  }, [theme]);

  const logout = () => {
    localStorage.removeItem("cmds_auth_token");
    localStorage.removeItem("cmds_auth_email");
    localStorage.removeItem("cmds_auth_role");
    localStorage.removeItem("cmds_auth_employee_id");
    toast.success("Signed out");
    navigate("/login", { replace: true });
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <div className="min-h-screen md:grid md:grid-cols-[280px_1fr]">
      <aside className="border-b border-slate-800/80 bg-slate-950/75 p-4 backdrop-blur md:sticky md:top-0 md:h-screen md:border-b-0 md:border-r">
        <div className="rounded-3xl border border-slate-700/60 bg-panel2/80 p-4 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] text-cyan-500 font-bold">Fintech Console</p>
          <p className="mt-1 text-xl font-bold text-ink">Cross Mule Detection</p>
          <p className="mt-2 text-sm leading-relaxed text-muted">Realtime anti-fraud command center for investigators and operators.</p>
        </div>

        <nav className="mt-5 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "block rounded-2xl px-4 py-3 text-base font-medium transition",
                  isActive
                    ? "border border-cyan-500/40 bg-cyan-500/20 text-cyan-100 shadow-glow"
                    : "border border-transparent text-slate-300 hover:border-slate-700 hover:bg-slate-800/80 hover:text-slate-100",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-6 space-y-2 rounded-2xl border border-slate-700/70 bg-slate-900/70 p-4">
          <button type="button" className="btn-secondary w-full" onClick={toggleTheme}>
            Switch to {theme === "dark" ? "Light" : "Dark"} Mode
          </button>
        </div>

        <button type="button" className="btn-secondary mt-6 w-full" onClick={logout}>
          Sign out
        </button>
      </aside>

      <main className="relative p-4 md:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-700/50 bg-slate-950/45 px-6 py-4 shadow-panel backdrop-blur">
          <div>
            <p className="text-sm uppercase tracking-[0.15em] font-semibold text-cyan-300">Operational overview</p>
            <p className="mt-1 text-base text-muted">Audit-ready fraud monitoring with report persistence and live observability.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm font-medium text-slate-300">
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/15 px-4 py-1.5 text-emerald-200 shadow-glow">
              API ready
            </span>
            <span className="rounded-full border border-cyan-500/30 bg-cyan-500/15 px-4 py-1.5 text-cyan-200 shadow-glow">
              Evidence archived
            </span>
          </div>
        </div>

        <div className="fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
