import Link from "next/link";
import Logo from "@/components/ui/Logo";
import Reveal from "@/components/ui/Reveal";

/* ───────────── NAV ───────────── */
function Nav() {
  return (
    <header className="sticky top-0 z-30 bg-bg/80 backdrop-blur-md border-b border-border/60">
      <div className="wrap h-20 flex items-center justify-between">
        <Logo size="md" />
        <nav className="hidden lg:flex items-center gap-9 text-[15px] text-ink-2">
          <a className="hover:text-ink transition" href="#tools">Tools</a>
          <a className="hover:text-ink transition" href="#how">How it works</a>
          <a className="hover:text-ink transition" href="#pricing">Pricing</a>
          <a className="hover:text-ink transition" href="#architecture">Architecture</a>
          <a className="hover:text-ink transition" href="#agencies">For Agencies</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/sign-in" className="text-[15px] text-ink-2 hover:text-ink transition px-3">Sign in</Link>
          <Link href="/sign-in" className="btn-primary !py-3 !px-6 text-[15px]">Start free</Link>
        </div>
      </div>
    </header>
  );
}

/* ───────────── HERO ───────────── */
function Hero() {
  return (
    <section className="relative overflow-hidden bg-hero-wash">
      {/* drifting blobs */}
      <span className="blob" style={{ left: "-8%", top: "-6%", width: 500, height: 500, background: "radial-gradient(closest-side, rgba(255,181,167,0.55), transparent)" }} />
      <span className="blob" style={{ right: "-4%", top: "-2%", width: 420, height: 420, background: "radial-gradient(closest-side, rgba(224,213,247,0.55), transparent)", animationDelay: "-6s" }} />
      <span className="blob" style={{ right: "8%", bottom: "-14%", width: 600, height: 600, background: "radial-gradient(closest-side, rgba(253,240,200,0.55), transparent)", animationDelay: "-12s" }} />

      <div className="wrap relative pt-20 pb-24 md:pt-28 md:pb-32 text-center">
        <div className="hero-rise hero-rise-1 pill mx-auto">
          <span className="inline-flex items-center rounded-pill bg-ink text-surface px-2 py-0.5 text-[11px] tracking-[0.12em] font-semibold">NEW</span>
          <span>Private beta is open · licensed creator persona</span>
        </div>

        <h1 className="hero-rise hero-rise-2 mt-8 font-bold tracking-[-0.03em] leading-[0.98] text-[64px] md:text-[104px] text-ink">
          Sound like<br />Tanmay Bhat.
        </h1>

        <p className="hero-rise hero-rise-3 mt-9 mx-auto max-w-[720px] text-body-l text-ink-2 leading-relaxed">
          A licensed creator-persona platform that ingests the full digital footprint of India's
          sharpest voice and powers three creator tools. Built with consent. Shipped with citations.
        </p>

        <div className="hero-rise hero-rise-4 mt-10 flex items-center justify-center gap-3 flex-wrap">
          <Link href="/sign-in" className="btn-primary">Try it for yourself →</Link>
          <a href="#demo" className="btn-ghost">Watch the demo</a>
        </div>

        <p className="hero-rise hero-rise-5 mt-8 text-[14px] text-ink-3">
          Licensed directly from Tanmay · 500+ hours of corpus · Built in Mumbai &amp; Bangalore
        </p>
      </div>
    </section>
  );
}

/* ───────────── TOOLS ───────────── */
function Tools() {
  const tools = [
    { n: "01", title: "Content Generation", body: "Feed an idea, get a Tanmay-voiced script with rationale. The forgiving MVP.", gradient: "bg-gradient-sunrise", href: "/app/content" },
    { n: "02", title: "Ad Generation", body: "Structured brief goes in. Scene-by-scene ad comes out. Brand-safety gate included.", gradient: "bg-gradient-twilight", href: "/app/ads" },
    { n: "03", title: "How Would Tanmay Answer", body: "Ask anything. Grounded, cited, or an honest 'he has not spoken on this'.", gradient: "bg-gradient-sage", href: "/app/qa" },
  ];
  return (
    <section id="tools" className="py-28 bg-bg">
      <div className="wrap">
        <Reveal className="text-center max-w-[800px] mx-auto">
          <div className="caption">THREE TOOLS</div>
          <h2 className="mt-4 font-bold tracking-[-0.02em] leading-[1.08] text-[48px] md:text-[56px] text-ink">
            One persona core, three ways to create.
          </h2>
          <p className="mt-6 text-body-l text-ink-2 leading-relaxed">
            Every tab talks to the same knowledge store and persona engine. Different prompt
            strategy. Different retrieval shape. Different output.
          </p>
        </Reveal>

        <div className="mt-14 grid md:grid-cols-3 gap-6">
          {tools.map((t, i) => (
            <Reveal
              key={t.n}
              delay={((i + 1) as 1 | 2 | 3)}
              className="card overflow-hidden group transition hover:-translate-y-1 hover:shadow-card-lg"
            >
              <Link href={t.href} className="block">
                <div className={`${t.gradient} h-[180px] px-7 pt-10`}>
                  <div className="font-bold text-[96px] leading-none tracking-[-0.04em] text-ink/80">{t.n}</div>
                </div>
                <div className="px-7 py-7">
                  <h3 className="text-h3 text-ink">{t.title}</h3>
                  <p className="mt-3 text-body text-ink-2 leading-relaxed">{t.body}</p>
                  <div className="mt-8 text-[15px] font-medium text-coral-deep group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                    Explore →
                  </div>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────── HOW IT WORKS ───────────── */
function HowItWorks() {
  const steps = [
    { n: "01", bg: "bg-coral/25", title: "Ingest", body: "yt-dlp, Apify, and RSS pull videos, tweets, threads, reels, podcasts into R2." },
    { n: "02", bg: "bg-lavender/70", title: "Transcribe", body: "Deepgram diarizes every minute. Only Tanmay's utterances survive." },
    { n: "03", bg: "bg-mint/80", title: "Embed & Tag", body: "Voyage-3 embeddings, Claude Haiku tags, Qdrant indexes. Style exemplars saved." },
    { n: "04", bg: "bg-butter", title: "Generate", body: "Hybrid retrieval → Cohere rerank → persona prompt → Claude Sonnet 4.6." },
  ];
  return (
    <section id="how" className="py-28 bg-surface">
      <div className="wrap">
        <Reveal className="text-center max-w-[800px] mx-auto">
          <div className="caption">HOW IT WORKS</div>
          <h2 className="mt-4 font-bold tracking-[-0.02em] leading-[1.08] text-[40px] md:text-[52px] text-ink">
            Four stages. Forty years of Tanmay.
          </h2>
        </Reveal>

        <div className="mt-14 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {steps.map((s, i) => (
            <Reveal
              key={s.n}
              delay={((i + 1) as 1 | 2 | 3 | 4)}
              className="card p-7 transition hover:-translate-y-1"
            >
              <div className={`h-16 w-16 rounded-2xl grid place-items-center ${s.bg}`}>
                <span className="font-bold text-[22px] text-ink tracking-tight">{s.n}</span>
              </div>
              <h3 className="mt-7 text-h3 text-ink">{s.title}</h3>
              <p className="mt-3 text-body text-ink-2 leading-relaxed">{s.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────── FEATURES ───────────── */
function Features() {
  const feats = [
    { bg: "bg-coral/25", title: "Source-grounded citations", body: "Click any claim, jump to the exact second in a podcast." },
    { bg: "bg-lavender/70", title: "Tone dial", body: "Roast, chaos, depth, and Hinglish ratio — all tunable." },
    { bg: "bg-mint/80", title: "Voice output (premium)", body: "Licensed ElevenLabs clone with watermarking baked in." },
    { bg: "bg-butter", title: "Brand safety guardrails", body: "Category conflicts flagged before you waste a generation." },
  ];
  return (
    <section className="py-28 bg-bg">
      <div className="wrap grid lg:grid-cols-[520px_1fr] gap-16 items-start">
        <Reveal>
          <div className="caption">WHAT YOU GET</div>
          <h2 className="mt-4 font-bold tracking-[-0.02em] leading-[1.05] text-[44px] md:text-[56px] text-ink">
            Built like a product, not a demo.
          </h2>
          <p className="mt-6 text-body-l text-ink-2 leading-relaxed">
            Streaming outputs, clickable citations, tone dial, export to Markdown or Fountain, a
            brand-safety gate that actually flags conflicts, and an honest refusal when Tanmay
            hasn't touched a topic.
          </p>
        </Reveal>

        <div className="space-y-3">
          {feats.map((f, i) => (
            <Reveal
              key={f.title}
              delay={((i + 1) as 1 | 2 | 3 | 4)}
              className="card flex items-start gap-5 p-5"
            >
              <div className={`h-12 w-12 rounded-xl shrink-0 ${f.bg}`} />
              <div className="min-w-0">
                <div className="text-[18px] font-semibold text-ink">{f.title}</div>
                <div className="mt-1 text-body text-ink-2">{f.body}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ───────────── BIG CTA ───────────── */
function BigCta() {
  return (
    <section id="pricing" className="py-16 bg-bg">
      <div className="wrap">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl bg-gradient-blossom p-12 md:p-20 text-center">
            <span className="absolute -left-20 top-24 h-[500px] w-[500px] rounded-full bg-blush/40 blur-3xl pointer-events-none" />
            <span className="absolute -right-10 -top-20 h-[400px] w-[400px] rounded-full bg-lavender/50 blur-3xl pointer-events-none" />
            <h2 className="relative font-bold tracking-[-0.02em] leading-[1.05] text-[40px] md:text-[60px] text-ink max-w-[900px] mx-auto">
              Start writing like Tanmay today.
            </h2>
            <p className="relative mt-6 max-w-[520px] mx-auto text-body-l text-ink-2">
              Free forever on the first 10 generations. No card required.
            </p>
            <div className="relative mt-9 flex items-center justify-center gap-3 flex-wrap">
              <Link href="/sign-in" className="btn-primary">Start for free →</Link>
              <a href="#demo" className="btn-outline">Book a demo</a>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ───────────── FOOTER ───────────── */
function Footer() {
  return (
    <footer className="pt-20 pb-10 bg-bg border-t border-border/60">
      <div className="wrap grid md:grid-cols-[1.3fr_1fr_1fr_1fr] gap-10">
        <div>
          <Logo size="md" />
          <p className="mt-5 text-body text-ink-2 max-w-xs leading-relaxed">
            A licensed creator-persona platform. Built in India. Shipped with consent, citations,
            and a soft spot for Hinglish.
          </p>
        </div>
        <FooterCol title="PRODUCT" links={["Content", "Ads", "Q&A", "Pricing"]} />
        <FooterCol title="COMPANY" links={["About", "Blog", "Careers", "Press"]} />
        <FooterCol title="LEGAL" links={["License", "Privacy", "Terms", "DPA"]} />
      </div>
      <div className="wrap mt-14 pt-6 border-t border-border/60 flex justify-between items-center text-[14px] text-ink-3">
        <span>© 2026 Create with Tanmay. Made with warmth in Mumbai.</span>
        <span>Instagram · YouTube · X · LinkedIn</span>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: string[] }) {
  return (
    <div>
      <div className="caption !text-ink-3">{title}</div>
      <ul className="mt-5 space-y-3 text-body text-ink-2">
        {links.map((l) => (
          <li key={l}><a href="#" className="hover:text-ink transition">{l}</a></li>
        ))}
      </ul>
    </div>
  );
}

export default function Landing() {
  return (
    <>
      <Nav />
      <Hero />
      <Tools />
      <HowItWorks />
      <Features />
      <BigCta />
      <Footer />
    </>
  );
}
