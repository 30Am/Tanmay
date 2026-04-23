"use client";

import type { ToneDial as ToneDialT } from "@/lib/types";

interface Props {
  value: ToneDialT;
  onChange: (t: ToneDialT) => void;
}

const DIMENSIONS: { key: keyof ToneDialT; label: string; low: string; high: string }[] = [
  { key: "roast_level", label: "Roast", low: "Sincere", high: "Sharp" },
  { key: "chaos", label: "Chaos", low: "Structured", high: "Tangential" },
  { key: "depth", label: "Depth", low: "Surface", high: "Deep cut" },
  { key: "hinglish_ratio", label: "Hinglish", low: "English", high: "Bhai bhai" },
];

export default function ToneDial({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-2 gap-x-6 gap-y-4">
      {DIMENSIONS.map((d) => (
        <div key={d.key}>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-[12px] font-medium text-ink">{d.label}</label>
            <span className="text-[10px] font-mono text-inkSubtle">
              {Math.round((value[d.key] as number) * 100)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={value[d.key]}
            onChange={(e) => onChange({ ...value, [d.key]: parseFloat(e.target.value) })}
            className="w-full accent-pinkDeep"
          />
          <div className="flex items-center justify-between text-[10px] text-inkSubtle mt-1">
            <span>{d.low}</span>
            <span>{d.high}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
