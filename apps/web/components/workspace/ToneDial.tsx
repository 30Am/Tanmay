"use client";

import type { ToneDial as ToneDialT } from "@/lib/types";

interface Props {
  value: ToneDialT;
  onChange: (t: ToneDialT) => void;
}

const DIMS: { key: keyof ToneDialT; label: string; low: string; high: string }[] = [
  { key: "roast_level", label: "Roast", low: "Sincere", high: "Sharp" },
  { key: "chaos", label: "Chaos", low: "Structured", high: "Tangential" },
  { key: "depth", label: "Depth", low: "Surface", high: "Deep" },
  { key: "hinglish_ratio", label: "Hinglish", low: "English", high: "Bhai mode" },
];

export default function ToneDial({ value, onChange }: Props) {
  return (
    <div className="grid sm:grid-cols-2 gap-x-8 gap-y-5">
      {DIMS.map((d) => (
        <div key={d.key}>
          <div className="flex items-center justify-between mb-2">
            <label className="text-[13px] font-medium text-ink">{d.label}</label>
            <span className="text-[12px] font-mono text-ink-3">{Math.round(value[d.key] * 100)}</span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={value[d.key]}
            onChange={(e) => onChange({ ...value, [d.key]: parseFloat(e.target.value) })}
            className="w-full accent-coral-deep"
          />
          <div className="flex justify-between text-[11px] text-ink-3 mt-1">
            <span>{d.low}</span>
            <span>{d.high}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
