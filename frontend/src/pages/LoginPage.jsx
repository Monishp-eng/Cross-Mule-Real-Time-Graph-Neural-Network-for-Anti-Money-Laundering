import { useState } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { apiService } from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!username || !password) {
      toast.error("Enter username and password");
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.login({ identity: username, password });
      localStorage.setItem("cmds_auth_token", response.access_token);
      localStorage.setItem("cmds_auth_email", response.user?.email || username);
      localStorage.setItem("cmds_auth_role", response.user?.role || "ANALYST");
      localStorage.setItem("cmds_auth_employee_id", response.user?.employee_id || "");
      toast.success("Welcome back");
      navigate("/", { replace: true });
    } catch (error) {
      toast.error(error.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-6xl items-center gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="relative overflow-hidden rounded-[2rem] border border-slate-700/50 bg-slate-950/50 p-8 shadow-panel backdrop-blur">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.18),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(245,158,11,0.12),transparent_28%)]" />
          <div className="relative max-w-xl space-y-6">
            <p className="text-sm uppercase tracking-[0.15em] font-semibold text-cyan-300">Cross Mule Detection</p>
            <h1 className="text-4xl font-extrabold leading-tight text-ink md:text-5xl lg:text-6xl">Fraud operations with evidence, context, and speed.</h1>
            <p className="max-w-lg text-base leading-relaxed text-muted md:text-lg">
              Review transactions, inspect graph-linked behavior, and validate alert decisions in a single control plane.
            </p>

            <div className="grid gap-4 sm:grid-cols-3 mt-4">
              <div className="rounded-2xl border border-slate-700/60 bg-slate-900/70 p-5 shadow-panel">
                <p className="text-sm font-semibold uppercase tracking-[0.15em] text-muted">Channels</p>
                <p className="mt-2 text-xl font-bold text-ink">Mobile, Web, ATM, UPI</p>
              </div>
              <div className="rounded-2xl border border-slate-700/60 bg-slate-900/70 p-5 shadow-panel">
                <p className="text-sm font-semibold uppercase tracking-[0.15em] text-muted">Evidence</p>
                <p className="mt-2 text-xl font-bold text-ink">Load + governance</p>
              </div>
              <div className="rounded-2xl border border-slate-700/60 bg-slate-900/70 p-5 shadow-panel">
                <p className="text-sm font-semibold uppercase tracking-[0.15em] text-muted">Mode</p>
                <p className="mt-2 text-xl font-bold text-ink">Audit ready</p>
              </div>
            </div>
          </div>
        </section>

        <form onSubmit={onSubmit} className="card space-y-6 p-8 md:p-10">
          <div>
            <p className="text-sm uppercase tracking-[0.15em] font-semibold text-cyan-300">Access Portal</p>
            <h2 className="mt-2 text-3xl font-extrabold text-ink">Sign in</h2>
            <p className="mt-2 text-base text-muted">Internal bank staff login only. Use your Employee ID or bank email.</p>
          </div>

          <label className="block text-base font-medium text-muted">
            Employee ID / Email
            <input
              className="input mt-2 py-3 text-base"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="EMP-1001 or analyst@bank.local"
            />
          </label>

          <label className="block text-base font-medium text-muted">
            Password
            <input
              type="password"
              className="input mt-2 py-3 text-base"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </label>

          <button type="submit" className="btn w-full py-3 text-base font-bold shadow-glow" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-center text-base text-muted">
            Need an account?{" "}
            <Link to="/signup" className="font-semibold text-cyan-300 hover:text-cyan-100 transition">
              Sign up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
