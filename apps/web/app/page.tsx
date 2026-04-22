import Link from "next/link";

const tabs = [
  {
    href: "/content",
    title: "Content Generation",
    tagline: "Type an idea. Get a script and a Tanmay-flavored point of view.",
  },
  {
    href: "/ad",
    title: "Ad Generation",
    tagline: "Structured product input. A scene-by-scene script with rationale.",
  },
  {
    href: "/qa",
    title: "How Would Tanmay Answer",
    tagline: "Grounded in his actual words. Refuses honestly when he hasn't spoken on it.",
  },
];

export default function Home() {
  return (
    <section>
      <div className="mb-12 max-w-3xl">
        <div className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-accent">Project Blueprint v0.1</div>
        <h1 className="mb-4 text-5xl font-bold tracking-tight">Create with Tanmay</h1>
        <p className="text-lg text-muted">
          A licensed creator-persona platform. Three creator tools, one persona core. Each tab talks to the same
          knowledge store with a different retrieval policy and output schema.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {tabs.map((t) => (
          <Link
            key={t.href}
            href={t.href}
            className="block rounded-xl border border-border bg-panel p-6 transition hover:border-accent"
          >
            <div className="mb-2 text-sm uppercase tracking-[0.15em] text-accentGreen">{t.title}</div>
            <div className="text-sm text-muted">{t.tagline}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
