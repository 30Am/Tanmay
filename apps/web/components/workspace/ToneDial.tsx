"use client";

import type { ToneDial as ToneDialT } from "@/lib/types";

interface Props {
  value: ToneDialT;
  onChange: (t: ToneDialT) => void;
  onReset?: () => void;
}

/** 4 horizontal tone sliders, each with its own gradient-colored fill (matches Figma Content tab). */
const DIMS: { key: keyof ToneDialT; label: string; track: string }[] = [
  { key: "roast_level", label: "Roast", track: "bg-gradient-to-r from-coral to-coral-deep" },
  { key: "chaos", label: "Chaos", track: "bg-gradient-to-r from-periwinkle to-lavender" },
  { key: "depth", label: "Depth", track: "bg-gradient-to-r from-mint to-aqua" },
  { key: "hinglish_ratio", label: "Hinglish", track: "bg-gradient-to-r from-peach to-blush" },
];

export default function ToneDial({ value, onChange, onReset }: Props) {
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <label className="text-[14px] font-medium text-ink">Tone dial</label>
        {onReset && (
          <button
            type="button"
            onClick={onReset}
            className="text-[13px] text-coral-deep hover:underline"
          >
            Reset
          </button>
        )}
      </div>

      <div className="space-y-4">
        {DIMS.map((d) => {
          const pct = Math.round(value[d.key] * 100);
          return (
            <div key={d.key}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[14px] text-ink">{d.label}</span>
                <span className="text-[13px] text-ink-3 font-mono tabular-nums">{pct}</span>
              </div>
              <div className="relative h-2 rounded-pill bg-border overflow-hidden">
                <div
                  className={`absolute inset-y-0 left-0 rounded-pill ${d.track}`}
                  style={{ width: `${pct}%` }}
                />
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={value[d.key]}
                  onChange={(e) => onChange({ ...value, [d.key]: parseFloat(e.target.value) })}
                  className="absolute inset-0 w-full opacity-0 cursor-pointer"
                  aria-label={d.label}
                />
                <div
                  className="absolute top-1/2 -translate-y-1/2 h-[18px] w-[18px] rounded-full bg-surface border border-border shadow-card pointer-events-none"
                  style={{ left: `calc(${pct}% - 9px)` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
