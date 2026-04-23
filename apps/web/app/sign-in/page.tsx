"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { signIn } from "next-auth/react";
import { Loader2 } from "lucide-react";
import Logo from "@/components/ui/Logo";

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInInner />
    </Suspense>
  );
}

function SignInInner() {
  const params = useSearchParams();
  const callbackUrl = params.get("next") || params.get("callbackUrl") || "/app";
  const urlErr = params.get("error");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState<null | "email" | "google" | "apple">(null);
  const [err, setErr] = useState<string | null>(
    urlErr ? readableAuthError(urlErr) : null,
  );

  async function handleEmail(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading("email");
    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
      callbackUrl,
    });
    setLoading(null);
    if (!res || res.error) {
      setErr(
        res?.error === "CredentialsSignin"
          ? "Couldn't sign you in with that email / password."
          : readableAuthError(res?.error ?? "Something went wrong"),
      );
      return;
    }
    // On success, redirect in the browser
    window.location.href = res.url ?? callbackUrl;
  }

  async function handleOAuth(provider: "google" | "apple") {
    setErr(null);
    setLoading(provider);
    await signIn(provider, { callbackUrl });
    // signIn handles the redirect itself; setLoading off in case of early return
    setLoading(null);
  }

  return (
    <div className="min-h-screen grid md:grid-cols-2">
      {/* ───── Left: gradient visual + testimonial ───── */}
      <section className="relative overflow-hidden bg-auth-wash">
        <span className="absolute -top-24 -left-24 h-[400px] w-[400px] rounded-full bg-lilac/50 blur-3xl pointer-events-none" />
        <span className="absolute top-32 -right-24 h-[500px] w-[500px] rounded-full bg-blush/40 blur-3xl pointer-events-none" />

        <div className="relative h-full flex flex-col p-14">
          <Link href="/"><Logo size="md" /></Link>

          <div className="mt-24 max-w-[540px]">
            <h1 className="font-bold tracking-[-0.03em] leading-[1.02] text-[58px] text-ink">
              Welcome back.<br />Create with voice.
            </h1>
            <p className="mt-7 text-body-l text-ink-2 leading-relaxed max-w-[440px]">
              Pick up where you left off. All your drafts, citations, and tone dials are right
              where you left them.
            </p>
          </div>

          <div className="mt-auto card p-9 max-w-[540px]">
            <p className="text-body-l text-ink leading-relaxed">
              "The first persona platform I trust enough to actually ship from. Cited, licensed,
              on-brand."
            </p>
            <div className="mt-6 flex items-center gap-3">
              <span className="h-10 w-10 rounded-full bg-gradient-sunrise" />
              <div>
                <div className="text-[15px] font-semibold">Riya Menon</div>
                <div className="text-[13px] text-ink-3">Creator, 1.2M subs</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ───── Right: form ───── */}
      <section className="bg-bg grid place-items-center px-6 py-12">
        <div className="w-full max-w-[440px]">
          <div className="caption">SIGN IN</div>
          <h2 className="mt-3 font-bold tracking-[-0.02em] leading-[1.1] text-[36px] text-ink">
            Sign in to your workspace
          </h2>
          <p className="mt-3 text-body text-ink-2">
            Use Google or continue with a demo account.
          </p>

          {err && (
            <div className="mt-5 rounded-2xl bg-coral/15 border border-coral/40 p-4 text-[14px] text-ink">
              {err}
            </div>
          )}

          <div className="mt-6 space-y-3">
            <button
              onClick={() => handleOAuth("google")}
              disabled={!!loading}
              className="w-full rounded-pill bg-surface border border-border px-5 py-3.5 flex items-center justify-center gap-3 text-body font-medium text-ink hover:bg-bg transition disabled:opacity-60"
            >
              {loading === "google"
                ? <><Loader2 size={16} className="animate-spin" />Redirecting to Google…</>
                : <><GoogleIcon />Continue with Google</>}
            </button>
            <button
              onClick={() => handleOAuth("apple")}
              disabled={!!loading}
              className="w-full rounded-pill bg-surface border border-border px-5 py-3.5 flex items-center justify-center gap-3 text-body font-medium text-ink hover:bg-bg transition disabled:opacity-60"
            >
              <AppleIcon />Continue with Apple
            </button>
          </div>

          <div className="my-8 flex items-center gap-4">
            <span className="flex-1 h-px bg-border" />
            <span className="text-[13px] text-ink-3">or</span>
            <span className="flex-1 h-px bg-border" />
          </div>

          <form onSubmit={handleEmail} className="space-y-5">
            <div>
              <label className="field-label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                className="field"
                placeholder="demo@withtanmay.com"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="field-label !mb-0" htmlFor="password">Password</label>
                <a href="#" className="text-[13px] font-medium text-coral-deep hover:underline">
                  Forgot?
                </a>
              </div>
              <input
                id="password"
                type="password"
                className="field"
                placeholder="demo"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <label className="flex items-center gap-2.5 text-body text-ink-2 select-none pt-2">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-[18px] w-[18px] rounded-[4px] border-border accent-ink"
              />
              Keep me signed in on this device
            </label>

            <button
              type="submit"
              disabled={!!loading || !email || !password}
              className="btn-primary w-full mt-3 !py-4"
            >
              {loading === "email"
                ? <><Loader2 size={16} className="mr-2 animate-spin" />Signing you in…</>
                : "Sign in →"}
            </button>
          </form>

          <div className="mt-6 rounded-xl bg-butter/50 border border-border px-4 py-3 text-[13px] text-ink-2">
            <span className="font-semibold text-ink">Demo creds:</span>{" "}
            <span className="font-mono">demo@withtanmay.com</span>
            <span className="text-ink-3"> / </span>
            <span className="font-mono">demo</span>
          </div>

          <div className="mt-6 text-center text-body text-ink-2">
            New here?{" "}
            <a href="#" className="font-semibold text-coral-deep hover:underline">
              Create an account
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

/* Inline icons so we don't pay for an icon lib roundtrip */
function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.6l6.7-6.7C35.6 2.5 30.2 0 24 0 14.6 0 6.5 5.4 2.6 13.3l7.9 6.1C12.3 13.3 17.6 9.5 24 9.5z"/>
      <path fill="#4285F4" d="M46.5 24.6c0-1.6-.1-3.1-.4-4.6H24v9.1h12.7c-.6 3-2.3 5.5-4.8 7.2l7.6 5.9c4.4-4.1 7-10.1 7-17.6z"/>
      <path fill="#FBBC05" d="M10.5 28.6c-.5-1.4-.8-3-.8-4.6s.3-3.2.8-4.6l-7.9-6.1C1 16.7 0 20.2 0 24s1 7.3 2.6 10.7l7.9-6.1z"/>
      <path fill="#34A853" d="M24 48c6.5 0 11.9-2.1 15.9-5.8l-7.6-5.9c-2.1 1.4-4.9 2.3-8.3 2.3-6.4 0-11.7-3.8-13.5-9.9l-7.9 6.1C6.5 42.6 14.6 48 24 48z"/>
    </svg>
  );
}

function AppleIcon() {
  return (
    <svg width="16" height="18" viewBox="0 0 16 18" fill="currentColor" aria-hidden="true">
      <path d="M13.1 9.45c0-2.18 1.78-3.23 1.86-3.28-1.01-1.48-2.6-1.68-3.15-1.7-1.34-.13-2.61.79-3.29.79-.69 0-1.73-.77-2.85-.75-1.46.02-2.82.86-3.57 2.17-1.53 2.65-.39 6.56 1.09 8.71.72 1.05 1.58 2.23 2.7 2.19 1.09-.04 1.5-.7 2.82-.7 1.31 0 1.68.7 2.83.68 1.17-.02 1.9-1.07 2.61-2.13.82-1.22 1.16-2.4 1.17-2.46-.03-.01-2.24-.86-2.22-3.42zm-2.2-6.28c.6-.73 1.01-1.74.9-2.75-.87.04-1.92.58-2.54 1.31-.56.64-1.05 1.67-.92 2.66.97.08 1.96-.49 2.56-1.22z"/>
    </svg>
  );
}

function readableAuthError(code: string): string {
  switch (code) {
    case "OAuthAccountNotLinked":
      return "An account with this email already exists. Try signing in another way.";
    case "AccessDenied":
      return "Access denied.";
    case "Configuration":
      return "OAuth isn't configured. Ask the admin to add GOOGLE_CLIENT_ID / SECRET.";
    default:
      return code.replace(/([a-z])([A-Z])/g, "$1 $2");
  }
}
