import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Page
        canvas: "#FDFBF8",
        ink: "#1A1A1F",
        inkMuted: "#5A5A66",
        inkSubtle: "#8C8C9A",
        line: "#ECE8E0",
        // Warm accents from the design
        peach: "#FFD9C5",
        peachDeep: "#FFB08A",
        salmon: "#FF8A6A",
        pink: "#FFBCD6",
        pinkDeep: "#FF8FB8",
        lavender: "#DCD3F2",
        lavenderDeep: "#B9A8E6",
        sky: "#D4E4F5",
        mint: "#CCEBE0",
        cream: "#FFF4E8",
        // Utility
        okGreen: "#A2E6C0",
        refuseRose: "#FFCCD2",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        serif: ["var(--font-fraunces)", "ui-serif", "Georgia", "serif"],
        mono: ["ui-monospace", "SF Mono", "Menlo", "monospace"],
      },
      backgroundImage: {
        "gradient-hero":
          "radial-gradient(60% 50% at 15% 20%, #FFE1CC 0%, transparent 60%), radial-gradient(60% 50% at 85% 10%, #FCE5F0 0%, transparent 60%), radial-gradient(70% 60% at 50% 90%, #E4D9F4 0%, transparent 70%)",
        "gradient-pill":
          "linear-gradient(90deg, #FFB08A 0%, #FF9EBE 50%, #C2A5E8 100%)",
        "gradient-card":
          "linear-gradient(135deg, #FFE9D9 0%, #FCE5F0 50%, #E4D9F4 100%)",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(30,22,16,0.04), 0 8px 24px rgba(30,22,16,0.06)",
        softLg: "0 2px 6px rgba(30,22,16,0.05), 0 20px 60px rgba(30,22,16,0.08)",
        insetSoft: "inset 0 1px 0 rgba(255,255,255,0.6)",
      },
      borderRadius: {
        pill: "9999px",
      },
    },
  },
  plugins: [],
};

export default config;
