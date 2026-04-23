import Link from "next/link";
import { AlignLeft, Box, MessageCircle } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* Greeting hero */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-sunrise p-12">
        <span className="absolute top-[-200px] right-[-100px] h-[500px] w-[500px] rounded-full bg-lilac/50 blur-3xl pointer-events-none" />
        <div className="relative">
          <div className="caption text-coral-deep">THURSDAY · 23 APR</div>
          <h1 className="mt-3 font-bold tracking-[-0.02em] leading-[1.05] text-[48px] text-ink">
            Good morning, Amlan.
          </h1>
          <p className="mt-4 max-w-[600px] text-body-l text-ink-2 leading-relaxed">
            You drafted 3 scripts yesterday. The ad about filter coffee got 82 on style-match.
            Let's do something new.
          </p>
        </div>
      </section>

      {/* Three tool tiles */}
      <section className="grid md:grid-cols-3 gap-5">
        <ToolTile
          n="TAB 01"
          title="Generate a script"
          body="Ideas in, Tanmay-voiced scripts out."
          icon={<AlignLeft size={22} className="text-ink" />}
          iconBg="bg-gradient-sunrise"
          href="/app/content"
        />
        <ToolTile
          n="TAB 02"
          title="Write an ad"
          body="Structured brief for scene-by-scene ads."
          icon={<Box size={22} className="text-ink" />}
          iconBg="bg-gradient-twilight"
          href="/app/ads"
        />
        <ToolTile
          n="TAB 03"
          title="Ask Tanmay"
          body="Cited answers, or an honest refusal."
          icon={<MessageCircle size={22} className="text-ink" />}
          iconBg="bg-gradient-sage"
          href="/app/qa"
        />
      </section>

      {/* Recent + Insight */}
      <section className="grid lg:grid-cols-[1fr_360px] gap-5">
        <div className="card p-7">
          <div className="flex items-center justify-between">
            <h2 className="text-h3 text-ink">Recent generations</h2>
            <Link href="#" className="text-[14px] font-medium text-coral-deep hover:underline">See all →</Link>
          </div>
          <ul className="mt-6 space-y-2">
            <RecentRow dot="bg-lavender" title="Filter Coffee ad — 45s hero cut" chip={<span className="chip-ads">Ads</span>} meta="12 min ago" score="Style 82" />
            <RecentRow dot="bg-coral/60" title="Reaction script — UPSC topper interview" chip={<span className="chip-content">Content</span>} meta="2 hours ago" score="Style 78" />
            <RecentRow dot="bg-mint" title="What does Tanmay think about IPL bidding?" chip={<span className="chip-qa">Q&A</span>} meta="Yesterday" score="3 citations" />
          </ul>
        </div>

        <div className="card bg-gradient-blossom relative overflow-hidden p-7">
          <span className="absolute inset-x-0 top-0 h-[300px] bg-gradient-to-b from-white/0 to-white/0" />
          <div className="flex flex-col h-full min-h-[380px] justify-end">
            <div className="caption text-coral-deep">TODAY'S TANMAY INSIGHT</div>
            <p className="mt-4 text-body-l leading-relaxed text-ink font-medium">
              "Callback humor is a bet on your audience's memory. Tanmay wins that bet 9 out of 10 times."
            </p>
            <div className="mt-7 flex items-end justify-between">
              <div>
                <div className="text-[12px] font-semibold tracking-[0.14em] text-ink-2">STYLE MATCH · 7-DAY AVG</div>
                <div className="mt-1.5 font-bold tracking-[-0.02em] text-[36px] text-ink">79%</div>
              </div>
              <Sparkline />
            </div>
          </div>
        </div>
      </section>

      {/* Usage bar */}
      <section className="card p-6 flex items-center gap-6 flex-wrap">
        <div className="min-w-[260px]">
          <div className="text-[15px] font-semibold text-ink">
            Pro plan · 1,250 of 2,000 generations this month
          </div>
          <div className="mt-1 text-[13px] text-ink-3">Resets on May 1, 2026</div>
        </div>
        <div className="flex-1 min-w-[240px] h-2 rounded-pill bg-border overflow-hidden">
          <div className="h-full bg-gradient-sunrise" style={{ width: "62%" }} />
        </div>
        <button className="btn-primary !py-2.5 !px-5 text-[14px]">Upgrade</button>
      </section>
    </div>
  );
}

function ToolTile({
  n,
  title,
  body,
  icon,
  iconBg,
  href,
}: {
  n: string;
  title: string;
  body: string;
  icon: React.ReactNode;
  iconBg: string;
  href: string;
}) {
  return (
    <Link href={href} className="card group p-7 transition hover:-translate-y-1 hover:shadow-card-lg">
      <div className="flex items-start justify-between">
        <div className={`h-12 w-12 rounded-2xl grid place-items-center ${iconBg}`}>{icon}</div>
        <div className="caption text-coral-deep">{n}</div>
      </div>
      <h3 className="mt-16 text-h3 text-ink">{title}</h3>
      <p className="mt-2 text-body text-ink-2">{body}</p>
    </Link>
  );
}

function RecentRow({
  dot,
  title,
  chip,
  meta,
  score,
}: {
  dot: string;
  title: string;
  chip: React.ReactNode;
  meta: string;
  score: string;
}) {
  return (
    <li className="flex items-center gap-4 rounded-xl hover:bg-bg px-3 py-3 -mx-3 transition cursor-pointer">
      <span className={`h-10 w-10 rounded-2xl shrink-0 ${dot}`} />
      <div className="flex-1 min-w-0">
        <div className="text-[15px] font-medium text-ink truncate">{title}</div>
        <div className="mt-1 flex items-center gap-2 text-[13px] text-ink-3">
          {chip}
          <span>·</span>
          <span>{meta}</span>
        </div>
      </div>
      <span className="chip-qa !bg-mint/60 shrink-0">{score}</span>
    </li>
  );
}

function Sparkline() {
  const bars = [20, 28, 18, 32, 22, 34, 38];
  return (
    <div className="flex items-end gap-1.5 h-10">
      {bars.map((h, i) => (
        <span
          key={i}
          className={`w-[10px] rounded-sm ${i === bars.length - 1 ? "bg-coral-deep" : "bg-ink/70"}`}
          style={{ height: `${h}px` }}
        />
      ))}
    </div>
  );
}
