import Link from "next/link";
import {
  AlignLeft,
  Box,
  Check,
  ChevronRight,
  Instagram,
  Linkedin,
  MessageSquare,
  Play,
  Quote,
  Sliders,
  Twitter,
  Waves,
  Youtube,
} from "lucide-react";

const Dot = ({ className = "" }: { className?: string }) => (
  <span className={`inline-block h-1.5 w-1.5 rounded-full ${className}`} />
);

/* ───────────────────── HEADER ───────────────────── */
function Header() {
  return (
    <header className="sticky top-0 z-30 backdrop-blur-md bg-white/60 border-b border-line">
      <div className="wrap flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="h-7 w-7 rounded-full bg-gradient-to-br from-pink to-lavender" />
          <span className="font-semibold tracking-tight text-[15px]">Create with Tanmay</span>
        </Link>
        <nav className="flex items-center gap-3">
          <Link href="/app" className="btn-ghost text-sm">Sign in</Link>
          <Link href="/app" className="btn-gradient text-sm">Get Started</Link>
        </nav>
      </div>
    </header>
  );
}

/* ───────────────────── HERO ───────────────────── */
function Hero() {
  return (
    <section className="bg-hero relative pt-14 pb-20 md:pt-20 md:pb-28">
      <div className="wrap text-center">
        <div className="pill mx-auto">
          <Dot className="bg-salmon" />
          <span>LIVE BETA</span>
          <span className="opacity-40">·</span>
          <span>HOW WOULD TANMAY ANSWER JUST SHIPPED</span>
        </div>
        <h1 className="font-serif text-5xl md:text-[76px] leading-[1.02] tracking-tight mt-6">
          Write like Tanmay.
          <br />
          <em className="text-gradient-warm italic font-light">Wit, warmth,</em>
          <br />
          <em className="text-gradient-warm italic font-light">whiplash timing.</em>
        </h1>
        <p className="mt-8 mx-auto max-w-xl text-inkMuted leading-relaxed">
          Three creator tools trained on ten years of podcasts, posts, PUBG streams, stage
          bits, and late-night WhatsApp takes. You bring the idea, we bring the voice that
          built AIB.
        </p>
        <div className="mt-9 flex items-center justify-center gap-3 flex-wrap">
          <Link href="/app" className="btn-gradient">Try it free, 20 drafts on us</Link>
          <a href="#demo" className="btn-ghost">
            <Play size={16} className="fill-current" />
            Watch 90-second demo
          </a>
        </div>

        {/* Polaroid */}
        <div className="mt-14 flex justify-center">
          <div className="polaroid w-[280px] md:w-[320px]">
            <div className="relative overflow-hidden rounded-lg bg-gradient-to-br from-[#3a1a12] via-[#5a1b18] to-[#2c1008] aspect-[3/4] flex items-end">
              <div className="absolute top-3 right-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-semibold text-white">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#4ade80]" />
                  STREAMING
                </span>
              </div>
              <svg viewBox="0 0 200 260" className="h-full w-full opacity-80">
                <defs>
                  <radialGradient id="face" cx="50%" cy="45%">
                    <stop offset="0%" stopColor="#ffcf9c" />
                    <stop offset="100%" stopColor="#2a0c06" />
                  </radialGradient>
                </defs>
                <ellipse cx="100" cy="110" rx="50" ry="60" fill="url(#face)" />
                <rect x="40" y="170" width="120" height="100" rx="10" fill="#0a0405" />
                <rect x="70" y="95" width="60" height="14" rx="6" fill="#1a0a05" />
              </svg>
              <div className="absolute bottom-3 left-3 right-3 rounded-xl bg-white/80 backdrop-blur px-3 py-2 flex items-center justify-between">
                <span className="text-[13px] font-semibold">Tanmay</span>
                <span className="text-[10px] text-inkSubtle font-mono">v3.2</span>
              </div>
            </div>
          </div>
        </div>

        {/* Archive chips */}
        <div className="mt-14 text-center">
          <div className="text-[11px] tracking-[0.28em] text-inkSubtle font-semibold">IN THE ARCHIVE</div>
          <div className="mt-4 flex flex-wrap justify-center gap-5 text-sm text-inkMuted">
            <span className="inline-flex items-center gap-2"><Dot className="bg-salmon/70" />Honestly Podcast</span>
            <span className="inline-flex items-center gap-2"><Dot className="bg-pink/70" />AIB Vault</span>
            <span className="inline-flex items-center gap-2"><Dot className="bg-lavenderDeep/70" />Comicstaan</span>
          </div>
        </div>

        {/* Timeline */}
        <div className="mt-8 border-t border-line pt-5">
          <div className="wrap flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-[13px] text-inkMuted">
            <TimelineItem label="Honestly, ep 142" year="2024" />
            <TimelineItem label="AIB, Budget Roast" year="2016" />
            <TimelineItem label="Comicstaan S1" year="2018" />
            <TimelineItem label="PUBG late stream" year="2020" />
            <TimelineItem label="Learning streams" year="2022" />
          </div>
        </div>
      </div>
    </section>
  );
}

function TimelineItem({ label, year }: { label: string; year: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Dot className="bg-pinkDeep" />
      <span>{label}</span>
      <span className="font-mono text-[11px] text-inkSubtle">{year}</span>
    </span>
  );
}

/* ───────────────────── WORKSPACE PREVIEW ───────────────────── */
function WorkspacePreview() {
  return (
    <section id="demo" className="bg-soft py-14">
      <div className="wrap">
        <div className="workspace-card p-6 md:p-8 grid md:grid-cols-[220px_1fr] gap-6">
          <aside className="space-y-2">
            {[
              { dot: "bg-salmon/70", name: "Content Generation", active: true },
              { dot: "bg-sky", name: "Ad Generation" },
              { dot: "bg-lavender", name: "How Would Tanmay Answer" },
            ].map((t) => (
              <div
                key={t.name}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm ${
                  t.active ? "bg-cream/80 border border-line" : "hover:bg-canvas"
                }`}
              >
                <Dot className={`${t.dot} !h-2.5 !w-2.5`} />
                <span className="text-inkMuted">{t.name}</span>
              </div>
            ))}
          </aside>
          <div>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h3 className="font-serif text-xl">Morning routine, 60 sec hook</h3>
              <div className="flex gap-2">
                <span className="pill bg-lavender/20 border-lavender/40 text-inkMuted">
                  <Dot className="bg-lavenderDeep" />Tone: Podcast
                </span>
                <span className="pill bg-[#d4f0de]/40 border-okGreen/40 text-inkMuted">
                  <Dot className="bg-[#16a34a]" />Cleared
                </span>
              </div>
            </div>
            <div className="mt-5 rounded-2xl border border-line bg-canvas/70 p-5 text-sm text-inkMuted">
              Write a 60-second opener for a reel on why I stopped journaling. Keep it dry,
              a soft punchline, no life-coach energy.
            </div>
            <div className="mt-4 rounded-2xl border border-line bg-white p-5 text-[15px] leading-relaxed">
              Look, I tried journaling for six years. Six. Years. I have notebooks that
              start with "today I will be different" and end, eleven pages later, with a
              grocery list
              <CitePill>ep 84, 12:04</CitePill>. The truth is, I was writing to a version
              of me that didn't exist yet, and the real me was just, you know, hungry.
              <CitePill>Stage, BLR '23</CitePill>
            </div>
            <div className="mt-5 flex items-center justify-between text-sm text-inkMuted">
              <div className="flex gap-5">
                <button className="hover:text-ink">Regenerate</button>
                <button className="hover:text-ink">Show sources (4)</button>
              </div>
              <button className="btn-gradient !py-2 !px-5 !text-xs">Copy</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CitePill({ children }: { children: React.ReactNode }) {
  return (
    <span className="mx-1 inline-flex items-center rounded-md bg-cream border border-line px-1.5 py-0.5 font-mono text-[11px] text-inkMuted">
      {children}
    </span>
  );
}

/* ───────────────────── ABOUT TANMAY ───────────────────── */
function AboutTanmay() {
  return (
    <section className="bg-soft py-20">
      <div className="wrap grid md:grid-cols-2 gap-12 items-center">
        <div>
          <div className="pill"><Dot className="bg-salmon" />WHO YOU'RE CREATING WITH</div>
          <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4 leading-[1.08]">
            Ten years of takes. <em className="text-gradient-warm italic font-light">One very specific laugh.</em>
          </h2>
          <div className="mt-6 text-inkMuted leading-relaxed max-w-lg space-y-4">
            <p>
              Tanmay Bhat, comedian, podcaster, streamer, AIB co-founder, has spent a decade
              building a voice that's dry without being cold, warm without being sappy, and
              funny without trying too hard.
            </p>
            <p>
              We took every podcast, post, stream, and stage set we could get our hands on,
              and trained a model that knows the difference between a Sunday Honestly open
              and a Tuesday sponsor read. You bring the idea. He brings the timing.
            </p>
          </div>
          <dl className="mt-10 grid grid-cols-3 gap-8 max-w-lg">
            {[
              { value: "10+", label: "YEARS ON MIC" },
              { value: "4,200", label: "ARCHIVE MOMENTS" },
              { value: "142", label: "HONESTLY EPISODES" },
            ].map((s) => (
              <div key={s.label}>
                <dd className="font-serif text-4xl text-pinkDeep">{s.value}</dd>
                <dt className="mt-2 text-[11px] tracking-[0.18em] text-inkSubtle font-semibold">
                  {s.label}
                </dt>
              </div>
            ))}
          </dl>
        </div>
        <div className="flex justify-center">
          <div className="polaroid w-[300px] md:w-[340px]" style={{ transform: "rotate(2deg)" }}>
            <div className="relative overflow-hidden rounded-lg aspect-[4/5] bg-gradient-to-br from-[#d04a2a] via-[#a63920] to-[#3d1408] flex items-end">
              <div className="absolute top-3 right-3 flex items-center gap-1 text-white/90 text-[10px] font-mono">
                <span>LA50</span><span>·</span><span>Lifestyle Asia</span><span>·</span><span>202</span>
              </div>
              <div className="absolute top-8 left-3 text-white/70 text-[10px] leading-tight">
                <div className="font-semibold">TOKI</div>
                <div>PREMIUM</div>
                <div>CLUB SAKE</div>
                <div className="mt-2 font-semibold">PRESENTS</div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <svg viewBox="0 0 200 260" className="h-[85%] w-[85%] opacity-90">
                  <ellipse cx="100" cy="100" rx="55" ry="65" fill="#c9875d" />
                  <rect x="30" y="170" width="140" height="110" rx="10" fill="#0a0405" />
                  <rect x="70" y="92" width="60" height="14" rx="6" fill="#1a0a05" />
                </svg>
              </div>
              <div className="relative p-4 w-full">
                <div className="font-serif text-white text-3xl tracking-wide font-bold drop-shadow-lg">
                  TANMAY BHAT
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── TOOLKIT ───────────────────── */
function Toolkit() {
  const tools = [
    {
      tag: "TOOL 01",
      icon: <AlignLeft size={18} />,
      iconBg: "bg-salmon/20 text-salmon",
      name: "Content Generation",
      desc: "Reels, threads, newsletter drafts, and podcast cold-opens in Tanmay's voice, grounded in the actual archive.",
      href: "/app/content",
    },
    {
      tag: "TOOL 02",
      icon: <Box size={18} />,
      iconBg: "bg-sky text-[#3a7ab0]",
      name: "Ad Generation",
      desc: "Brand-safe ad reads and sponsorship hooks, tuned for tone and length, with guardrails baked in.",
      href: "/app/ad",
    },
    {
      tag: "TOOL 03",
      icon: <MessageSquare size={18} />,
      iconBg: "bg-lavender text-[#7d6ec6]",
      name: "How Would Tanmay Answer",
      desc: "Ask anything. Get a grounded, cited answer drawn from podcasts, posts, and stage moments, with the clips to match.",
      href: "/app/qa",
    },
  ];
  return (
    <section className="bg-hero py-20">
      <div className="wrap text-center">
        <div className="pill mx-auto">THE TOOLKIT</div>
        <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4">
          Three tools. <em className="text-inkSubtle italic font-light">One brain with good timing.</em>
        </h2>
        <p className="mt-5 text-inkMuted max-w-xl mx-auto">
          Each tool reads ten years of Tanmay before it writes a single line. You stay in
          the driver's seat, the voice stays unmistakably his.
        </p>
        <div className="mt-10 space-y-4 max-w-3xl mx-auto">
          {tools.map((t) => (
            <Link key={t.tag} href={t.href} className="card flex items-start gap-4 p-6 text-left group hover:shadow-softLg transition">
              <div className={`h-10 w-10 rounded-xl grid place-items-center ${t.iconBg}`}>{t.icon}</div>
              <div className="flex-1">
                <div className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle">{t.tag}</div>
                <div className="mt-1 font-semibold text-lg">{t.name}</div>
                <div className="mt-1 text-inkMuted text-sm">{t.desc}</div>
                <div className="mt-4 inline-flex items-center gap-1 text-sm text-ink group-hover:text-pinkDeep transition">
                  Learn more<ChevronRight size={14} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── HOW IT WORKS ───────────────────── */
function HowItWorks() {
  const steps = [
    { n: "01", title: "Pick a tool, drop a prompt.", body: "Choose Content, Ad, or How Would Tanmay Answer. Paste a topic, URL, or a rough scribble. Dial in tone and length." },
    { n: "02", title: "The archive reads first.", body: "We search every episode, post, and stage moment that matches, then draft with citations you can verify in one click." },
    { n: "03", title: "Refine, approve, publish.", body: "Nudge the tone, swap a line, preview it in voice. Export to your CMS, or copy straight into your scheduler." },
  ];
  return (
    <section className="bg-hero py-20">
      <div className="wrap text-center">
        <div className="pill mx-auto">HOW IT WORKS</div>
        <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4">
          From blank page to <em className="text-inkSubtle italic font-light">banger,</em> in three steps.
        </h2>
        <p className="mt-5 text-inkMuted max-w-xl mx-auto">
          The archive does the reading. The model does the scaffolding. You do the last 5%, which is, famously, the whole point.
        </p>
        <div className="mt-12 space-y-5 max-w-3xl mx-auto">
          {steps.map((s) => (
            <div key={s.n} className="card-soft p-6 text-left">
              <div className="font-serif text-5xl text-peachDeep">{s.n}</div>
              <hr className="mt-3 border-line" />
              <div className="mt-4 font-semibold">{s.title}</div>
              <div className="mt-1 text-inkMuted text-sm">{s.body}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── FEATURES ───────────────────── */
function Features() {
  const features = [
    { icon: <AlignLeft size={18} />, bg: "bg-salmon/20 text-salmon", title: "Source-grounded citations", body: "Every claim links back to the exact clip or post. No invented takes, no drift from the record." },
    { icon: <Sliders size={18} />, bg: "bg-sky text-[#3a7ab0]", title: "Tone dial", body: "Slide between podcast-thoughtful, stage-punchy, and Twitter-acid. Four tones, fully tunable." },
    { icon: <Waves size={18} />, bg: "bg-mint text-[#2e9a7a]", title: "Voice output preview", body: "Hear a draft in a voice-clone preview before you commit. Faster than re-recording three takes." },
    { icon: <Check size={18} />, bg: "bg-[#d4f0de] text-[#1f9d5a]", title: "Brand-safety guardrails", body: "Keyword and category blocks for sponsor reads. Flags risky claims before they leave the editor." },
    { icon: <Box size={18} />, bg: "bg-lavender text-[#7d6ec6]", title: "Timeline explorer", body: "Scrub the entire archive by year, show, or tag. Find the moment you half-remember in seconds." },
    { icon: <MessageSquare size={18} />, bg: "bg-peach text-peachDeep", title: "Chrome extension", body: "Draft replies, tweets, and captions in Tanmay's voice without leaving the tab you're already in." },
  ];
  return (
    <section className="bg-hero py-20">
      <div className="wrap text-center">
        <div className="pill mx-auto">FEATURES</div>
        <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4">
          Soft defaults. <em className="text-inkSubtle italic font-light">Serious knobs.</em>
        </h2>
        <p className="mt-5 text-inkMuted max-w-xl mx-auto">
          Everything a working creator needs on a Tuesday deadline. Nothing that gets in the way at 2 AM.
        </p>
        <div className="mt-10 space-y-3 max-w-3xl mx-auto">
          {features.map((f) => (
            <div key={f.title} className="card-soft p-5 flex items-start gap-4 text-left">
              <div className={`h-9 w-9 rounded-xl grid place-items-center shrink-0 ${f.bg}`}>{f.icon}</div>
              <div>
                <div className="font-semibold">{f.title}</div>
                <div className="mt-1 text-sm text-inkMuted">{f.body}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── TESTIMONIAL ───────────────────── */
function Testimonial() {
  return (
    <section className="bg-hero py-16">
      <div className="wrap">
        <div className="card max-w-3xl mx-auto p-8 md:p-10">
          <Quote size={22} className="text-salmon" />
          <p className="font-serif text-2xl md:text-[28px] leading-[1.35] mt-4">
            I drafted two reels, an ad read, and a newsletter in the time it usually takes
            me to remember a quote. And every line sounds like <em>me</em>, not like a bot
            pretending to be me at a conference.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-pink to-lavender grid place-items-center text-[11px] font-semibold">TB</div>
            <div>
              <div className="font-semibold text-sm">Tanmay Bhat</div>
              <div className="text-xs text-inkSubtle">Creator, podcaster, reluctant beta tester</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── PRICING ───────────────────── */
function Pricing() {
  const plans = [
    { badge: "FREE", price: "₹0", per: "/ month", desc: "For exploring the tools and writing your first few drafts.", features: ["20 generations per month", "Content and Ad tools", "Source citations", "Community support"], cta: "Start free", variant: "ghost" as const },
    { badge: "PRO", tag: "Most popular", price: "₹999", per: "/ month", desc: "For working creators shipping weekly, across platforms.", features: ["Unlimited generations", "All three tools, including HWTA", "Tone dial and voice preview", "Chrome extension", "Priority support"], cta: "Go Pro", variant: "gradient" as const },
    { badge: "STUDIO", price: "₹3,499", per: "/ month", desc: "For teams, agencies, and anyone running a content calendar for multiple voices.", features: ["5 seats included", "Brand-safety guardrails", "Shared workspaces and approvals", "API access", "Dedicated onboarding"], cta: "Talk to us", variant: "ghost" as const },
  ];
  return (
    <section className="bg-hero py-20">
      <div className="wrap text-center">
        <div className="pill mx-auto">PRICING</div>
        <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4">
          Honest plans, <em className="text-inkSubtle italic font-light">priced in rupees.</em>
        </h2>
        <p className="mt-5 text-inkMuted max-w-xl mx-auto">
          Start free. Upgrade the week you realise you're shipping twice as much and thinking half as hard.
        </p>
        <div className="mt-10 space-y-5 max-w-3xl mx-auto">
          {plans.map((p) => (
            <div key={p.badge} className="card text-left p-7 md:p-8">
              <div className="flex items-center gap-3">
                <div className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle">{p.badge}</div>
                {p.tag && <span className="rounded-full bg-lavender/40 text-ink px-3 py-0.5 text-[11px] font-semibold">{p.tag}</span>}
              </div>
              <div className="mt-3 flex items-end gap-1">
                <span className="font-serif text-5xl">{p.price}</span>
                <span className="text-xs text-inkSubtle mb-2">{p.per}</span>
              </div>
              <p className="mt-2 text-inkMuted text-sm">{p.desc}</p>
              <ul className="mt-5 space-y-2.5">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <span className="mt-0.5 h-4 w-4 rounded-full bg-lavender/40 grid place-items-center">
                      <Check size={10} className="text-[#7d6ec6]" />
                    </span>
                    <span className="text-inkMuted">{f}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-7">
                {p.variant === "gradient" ? (
                  <Link href="/app" className="btn-gradient w-full">{p.cta}</Link>
                ) : (
                  <Link href="/app" className="w-full inline-flex items-center justify-center rounded-full border border-line bg-white py-3 px-5 text-sm font-medium hover:bg-canvas">{p.cta}</Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── CTA BANNER ───────────────────── */
function CtaBanner() {
  return (
    <section className="bg-hero py-16">
      <div className="wrap">
        <div className="rounded-[28px] border border-white/50 p-12 md:p-16 text-center shadow-softLg" style={{ background: "linear-gradient(135deg, #FFE9D9 0%, #FCE5F0 50%, #E4D9F4 100%)" }}>
          <span className="pill bg-white/70 border-white/70">READY WHEN YOU ARE</span>
          <h2 className="font-serif text-4xl md:text-5xl tracking-tight mt-4">
            Ready when you are, <em className="italic">boss.</em>
          </h2>
          <p className="mt-5 max-w-md mx-auto text-inkMuted">
            Spin up your first draft in under a minute. No credit card, no wait-list, no seven-step onboarding tour.
          </p>
          <Link href="/app" className="btn-gradient mt-8 inline-flex">Try it free</Link>
        </div>
      </div>
    </section>
  );
}

/* ───────────────────── FOOTER ───────────────────── */
function Footer() {
  return (
    <footer className="bg-hero pt-14 pb-10 border-t border-line">
      <div className="wrap grid md:grid-cols-[1.2fr_1fr_1fr_1fr] gap-10">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="h-7 w-7 rounded-full bg-gradient-to-br from-pink to-lavender" />
            <span className="font-semibold tracking-tight">Create with Tanmay</span>
          </div>
          <p className="mt-4 text-sm text-inkMuted max-w-xs">
            Creator tools built on an actual archive, not a vibe. Made in Mumbai.
          </p>
          <div className="mt-5 flex gap-2.5 text-inkMuted">
            {[Twitter, Instagram, Youtube, Linkedin].map((Icon, i) => (
              <a key={i} href="#" className="h-8 w-8 rounded-lg border border-line bg-white grid place-items-center hover:text-ink transition">
                <Icon size={14} />
              </a>
            ))}
          </div>
        </div>
        <FooterCol title="PRODUCT" links={["Content Generation", "Ad Generation", "How Would Tanmay Answer", "Chrome extension", "Changelog"]} />
        <FooterCol title="COMPANY" links={["About", "Blog", "Careers", "Press kit", "Contact"]} />
        <FooterCol title="RESOURCES" links={["Docs", "Prompt library", "Creator playbooks", "Status", "API"]} />
      </div>
      <div className="wrap mt-10 pt-6 border-t border-line flex justify-between items-center text-xs text-inkSubtle">
        <span>© 2026 Create with Tanmay. All rights reserved.</span>
        <span>Crafted in Mumbai, shipped from anywhere.</span>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: string[] }) {
  return (
    <div>
      <div className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle">{title}</div>
      <ul className="mt-4 space-y-2.5 text-sm text-inkMuted">
        {links.map((l) => (
          <li key={l}><a href="#" className="hover:text-ink transition">{l}</a></li>
        ))}
      </ul>
    </div>
  );
}

/* ───────────────────── PAGE ───────────────────── */
export default function LandingPage() {
  return (
    <>
      <Header />
      <Hero />
      <WorkspacePreview />
      <AboutTanmay />
      <Toolkit />
      <HowItWorks />
      <Features />
      <Testimonial />
      <Pricing />
      <CtaBanner />
      <Footer />
    </>
  );
}
