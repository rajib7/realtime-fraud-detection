import React, { useState } from "react";
import { ShieldCheck, ArrowRight, Copy } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const AUTH_IDS = {
  root: "login-screen",
  email: "input-login-email",
  password: "input-login-password",
  submit: "btn-login-submit",
  tabLogin: "tab-login",
  tabRegister: "tab-register",
  registerName: "input-register-name",
  registerEmail: "input-register-email",
  registerPassword: "input-register-password",
  btnRegister: "btn-register-submit",
  errorBox: "login-error",
};

const DEMO_ACCOUNTS = [
  { role: "admin", email: "admin@fraudops.io", password: "admin123", accent: "#00E5FF", caps: "start / stop simulator · inject fraud · manage all" },
  { role: "analyst", email: "analyst@fraudops.io", password: "analyst123", accent: "#FFB000", caps: "acknowledge alerts · read all data" },
  { role: "viewer", email: "viewer@fraudops.io", password: "viewer123", accent: "#94A3B8", caps: "read-only observability" },
];

export default function LoginScreen() {
  const { login, register, error } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
        toast.success("Signed in");
      } else {
        await register(email, password, name);
        toast.success("Account created — signed in as viewer");
      }
    } catch {
      /* error already surfaced in context */
    } finally {
      setBusy(false);
    }
  }

  function fillDemo(a) {
    setEmail(a.email);
    setPassword(a.password);
    setMode("login");
    toast(`Prefilled ${a.role} credentials`);
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast(`Copied: ${text}`);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div
      className="min-h-screen bg-[#0A0C10] text-[#F8FAFC] grid-backdrop flex items-center justify-center px-4 py-10"
      data-testid={AUTH_IDS.root}
    >
      <div className="w-full max-w-[980px] grid md:grid-cols-2 gap-6">
        {/* left: brand + demo credentials */}
        <div className="card-surface p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md border border-[#00E5FF]/40 bg-[#00E5FF]/10 flex items-center justify-center text-[#00E5FF]">
                <ShieldCheck size={20} />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.28em] text-[#64748B] font-mono">
                  use case 02 · fraudops
                </div>
                <div className="text-lg font-semibold tracking-tight">
                  Real-time Fraud Detection
                </div>
              </div>
            </div>
            <p className="mt-6 text-sm text-[#94A3B8] leading-relaxed">
              A control-room console for the fraud detection microservice
              demo. Sign in with a role to see how permissions gate
              simulator control, fraud injection, and alert acknowledgement.
            </p>
          </div>

          <div className="mt-8 space-y-2">
            <div className="text-[10px] uppercase tracking-[0.22em] text-[#64748B] font-mono">
              demo accounts · one-click prefill
            </div>
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.role}
                data-testid={`demo-account-${a.role}`}
                onClick={() => fillDemo(a)}
                className="w-full flex items-start gap-3 p-3 border border-[#222630] rounded hover:border-[#333A4A] bg-[#0f1218] hover:bg-[#181C24] transition-colors text-left group"
              >
                <span
                  className="chip"
                  style={{
                    color: a.accent,
                    background: `${a.accent}14`,
                    borderColor: `${a.accent}55`,
                  }}
                >
                  {a.role}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="font-mono text-[12px] text-[#F8FAFC] truncate">
                    {a.email}
                    <span className="text-[#64748B]"> · {a.password}</span>
                  </div>
                  <div className="text-[11px] text-[#64748B] mt-1">
                    {a.caps}
                  </div>
                </div>
                <span className="text-[#64748B] group-hover:text-[#00E5FF] transition-colors">
                  <ArrowRight size={14} />
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* right: form */}
        <div className="card-surface p-6 sm:p-8">
          <div className="flex gap-1 mb-6 bg-[#0f1218] border border-[#222630] rounded p-1 w-fit">
            <button
              data-testid={AUTH_IDS.tabLogin}
              onClick={() => setMode("login")}
              className={`px-4 py-1.5 rounded text-[11px] font-mono uppercase tracking-wider ${
                mode === "login"
                  ? "bg-[#181C24] text-[#00E5FF]"
                  : "text-[#64748B]"
              }`}
            >
              sign in
            </button>
            <button
              data-testid={AUTH_IDS.tabRegister}
              onClick={() => setMode("register")}
              className={`px-4 py-1.5 rounded text-[11px] font-mono uppercase tracking-wider ${
                mode === "register"
                  ? "bg-[#181C24] text-[#00E5FF]"
                  : "text-[#64748B]"
              }`}
            >
              create account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <Label className="text-[10px] uppercase tracking-[0.18em] text-[#94A3B8] font-mono">
                  full name
                </Label>
                <Input
                  data-testid={AUTH_IDS.registerName}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 bg-[#0A0C10] border-[#222630] font-mono text-sm h-10"
                />
              </div>
            )}
            <div>
              <Label className="text-[10px] uppercase tracking-[0.18em] text-[#94A3B8] font-mono">
                email
              </Label>
              <Input
                data-testid={mode === "login" ? AUTH_IDS.email : AUTH_IDS.registerEmail}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1 bg-[#0A0C10] border-[#222630] font-mono text-sm h-10"
              />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-[0.18em] text-[#94A3B8] font-mono">
                password
              </Label>
              <Input
                data-testid={mode === "login" ? AUTH_IDS.password : AUTH_IDS.registerPassword}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="mt-1 bg-[#0A0C10] border-[#222630] font-mono text-sm h-10"
              />
            </div>

            {error && (
              <div
                data-testid={AUTH_IDS.errorBox}
                className="p-3 rounded border border-[#FF3366]/40 bg-[#FF3366]/10 text-[#FF3366] text-xs font-mono"
              >
                {error}
              </div>
            )}

            <Button
              data-testid={mode === "login" ? AUTH_IDS.submit : AUTH_IDS.btnRegister}
              type="submit"
              disabled={busy}
              className="w-full bg-[#00E5FF] hover:bg-[#00E5FF]/90 text-[#0A0C10] font-mono uppercase tracking-wider text-xs h-10"
            >
              {mode === "login" ? "sign in" : "create account & sign in"}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-[#222630] flex flex-col gap-2">
            <div className="text-[11px] font-mono text-[#64748B]">
              new accounts start with role{" "}
              <span className="text-[#94A3B8]">viewer</span> (read-only). ask
              an admin to elevate.
            </div>
            <div className="text-[11px] font-mono text-[#64748B]">
              source archive:{" "}
              <a
                data-testid="download-tarball-link"
                href="/api/download/source.tar.gz"
                className="text-[#00E5FF] hover:underline"
                download
              >
                .tar.gz
              </a>
              {"  ·  "}
              <a
                data-testid="download-zip-link"
                href="/api/download/source.zip"
                className="text-[#00E5FF] hover:underline"
                download
              >
                .zip
              </a>
            </div>
            <div className="text-[11px] font-mono text-[#64748B]">
              demo assets:{" "}
              <a
                data-testid="download-video-link"
                href="/api/download/demo-video.webm"
                className="text-[#FFB000] hover:underline"
                download
              >
                walkthrough.webm
              </a>
              {"  ·  "}
              <a
                data-testid="download-screenshots-link"
                href="/api/download/screenshots.zip"
                className="text-[#FFB000] hover:underline"
                download
              >
                screenshots.zip
              </a>
              {"  ·  "}
              <a
                data-testid="download-presentation-link"
                href="/api/download/presentation.pptx"
                className="text-[#FFB000] hover:underline"
                download
              >
                slides.pptx
              </a>
              {"  ·  "}
              <a
                data-testid="download-presentation-pdf-link"
                href="/api/download/presentation.pdf"
                className="text-[#FFB000] hover:underline"
                download
              >
                slides.pdf
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
