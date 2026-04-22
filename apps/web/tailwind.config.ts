import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f1115",
        panel: "#161922",
        panel2: "#1d2130",
        accent: "#ff6b35",
        accentGreen: "#4ade80",
        accentBlue: "#60a5fa",
        accentPurple: "#c084fc",
        border: "#2a2f3d",
        muted: "#9aa3b2",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
