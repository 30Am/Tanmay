import Link from "next/link";
import Logo from "@/components/ui/Logo";

export default function SignIn() {
  return (
    <div className="min-h-screen grid md:grid-cols-2">
      {/* ───── Left: gradient visual + testimonial ───── */}
      <section className="relative overflow-hidden bg-auth-wash">
        <span className="absolute -top-24 -left-24 h-[400px] w-[400px] rounded-full bg-lilac/50 blur-3xl pointer-events-none" />
        <span className="absolute top-32 -right-24 h-[500px] w-[500px] rounded-full bg-blush/40 blur-3xl pointer-events-none" />

        <div className="relative h-full flex flex-col p-14">
          <Logo size="md" />

          <div className="mt-24 max-w-[540px]">
            <h1 className="font-bold tracking-[-0.03em] leading-[1.02] text-[58px] text-ink">
              Welcome back.<br />Create with voice.
            </h1>
            <p className="mt-7 text-body-l text-ink-2 leading-relaxed max-w-[440px]">
              Pick up where you left off. All your drafts, citations, and tone dials are right where
              you left them.
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
            Use your Google account or sign in with email.
          </p>

          <div className="mt-8 space-y-3">
            <OAuthButton provider="google" />
            <OAuthButton provider="apple" />
          </div>

          <div className="my-8 flex items-center gap-4">
            <span className="flex-1 h-px bg-border" />
            <span className="text-[13px] text-ink-3">or</span>
            <span className="flex-1 h-px bg-border" />
          </div>

          <form className="space-y-5">
            <div>
              <label className="field-label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                className="field"
                placeholder="amlan@withtanmay.com"
                defaultValue=""
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="field-label !mb-0" htmlFor="password">Password</label>
                <a href="#" className="text-[13px] font-medium text-coral-deep hover:underline">Forgot?</a>
              </div>
              <input
                id="password"
                type="password"
                className="field"
                placeholder="••••••••••"
              />
            </div>
            <label className="flex items-center gap-2.5 text-body text-ink-2 select-none pt-2">
              <input type="checkbox" className="h-[18px] w-[18px] rounded-[4px] border-border accent-ink" />
              Keep me signed in on this device
            </label>

            <Link href="/app" className="btn-primary w-full mt-3 !py-4">Sign in →</Link>
          </form>

          <div className="mt-7 text-center text-body text-ink-2">
            New here?{" "}
            <a href="#" className="font-semibold text-coral-deep hover:underline">Create an account</a>
          </div>
        </div>
      </section>
    </div>
  );
}

function OAuthButton({ provider }: { provider: "google" | "apple" }) {
  const label = provider === "google" ? "Continue with Google" : "Continue with Apple";
  return (
    <button className="w-full rounded-pill bg-surface border border-border px-5 py-3.5 flex items-center justify-center gap-3 text-body font-medium text-ink hover:bg-bg transition">
      <span className={`h-5 w-5 rounded-[6px] ${provider === "google" ? "bg-gradient-sunrise" : "bg-ink"}`} />
      {label}
    </button>
  );
}
