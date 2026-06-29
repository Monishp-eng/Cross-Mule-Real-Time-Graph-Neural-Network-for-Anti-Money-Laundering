import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { apiService } from "../services/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    if (!identity || !password) {
      toast.error("Enter email or employee ID and password");
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.signup({
        identity,
        password,
        full_name: fullName,
      });
      localStorage.setItem("cmds_auth_token", response.access_token);
      localStorage.setItem("cmds_auth_email", response.user?.email || identity);
      localStorage.setItem("cmds_auth_role", response.user?.role || "ANALYST");
      localStorage.setItem("cmds_auth_employee_id", response.user?.employee_id || "");
      toast.success("Account created");
      navigate("/", { replace: true });
    } catch (error) {
      toast.error(error.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-6xl items-center gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="relative overflow-hidden rounded-[2rem] border border-slate-700/50 bg-slate-950/50 p-8 shadow-panel backdrop-blur">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.18),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(34,211,238,0.12),transparent_30%)]" />
          <div className="relative max-w-xl space-y-5">
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Secure Access</p>
            <h1 className="text-4xl font-bold leading-tight text-ink md:text-5xl">Create your internal analyst access.</h1>
            <p className="max-w-lg text-sm leading-6 text-muted md:text-base">
              Onboard a bank analyst profile for fraud monitoring, investigations, and compliance workflows.
            </p>
          </div>
        </section>

        <form onSubmit={onSubmit} className="card space-y-4 p-6 md:p-8">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-emerald-300">Account Setup</p>
            <h2 className="mt-1 text-2xl font-bold text-ink">Sign up</h2>
            <p className="mt-1 text-sm text-muted">Internal bank users only. Use your staff email or employee ID.</p>
          </div>

          <label className="block text-sm text-muted">
            Full name
            <input
              className="input mt-1"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Alex Doe"
            />
          </label>

          <label className="block text-sm text-muted">
            Employee ID / Email
            <input
              className="input mt-1"
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
              placeholder="EMP-1002 or analyst@bank.local"
            />
          </label>

          <label className="block text-sm text-muted">
            Password
            <input
              type="password"
              className="input mt-1"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
            />
          </label>

          <button type="submit" className="btn w-full" disabled={loading}>
            {loading ? "Creating account..." : "Create account"}
          </button>

          <p className="text-center text-sm text-muted">
            Already registered?{" "}
            <Link to="/login" className="text-cyan-300 hover:text-cyan-200">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
