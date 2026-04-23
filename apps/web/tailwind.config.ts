import type { Config } from "tailwindcss";

/**
 * Design tokens from the Figma design system (01 · Design System).
 * File: Create with Tanmay — Product UI
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}",
    "./lib/**/*.{ts,tsx,js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm palette (from Figma Color Tokens)
        peach: "#FFD4B8",
        coral: "#FFB5A7",
        blush: "#F8CDDA",
        lavender: "#E0D5F7",
        periwinkle: "#C7D7FA",
        lilac: "#EAD4F5",
        mint: "#D4EFDF",
        aqua: "#C8EAE4",
        butter: "#FDF0C8",

        // Surfaces
        bg: "#FAF7F2",
        surface: "#FFFFFF",
        border: "#ECE5D8",

        // Ink / text
        ink: {
          DEFAULT: "#2D2438", // darkAccent — primary ink / buttons
          2: "#4A4D58",
          3: "#8A8D98",
        },

        // Accent
        "coral-deep": "#E8755C",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        // from Typography · Inter
        display: ["96px", { lineHeight: "1", letterSpacing: "-0.03em", fontWeight: "700" }],
        h1: ["56px", { lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }],
        h2: ["36px", { lineHeight: "1.2", letterSpacing: "-0.015em", fontWeight: "700" }],
        h3: ["24px", { lineHeight: "1.3", letterSpacing: "-0.01em", fontWeight: "600" }],
        "body-l": ["18px", { lineHeight: "1.55", fontWeight: "400" }],
        body: ["16px", { lineHeight: "1.55", fontWeight: "400" }],
        caption: ["13px", { lineHeight: "1.25", letterSpacing: "0.12em", fontWeight: "600" }],
      },
      backgroundImage: {
        // Signature Gradients
        "gradient-sunrise": "linear-gradient(135deg, #FFD4B8 0%, #FFB5A7 50%, #F8CDDA 100%)",
        "gradient-twilight": "linear-gradient(135deg, #E0D5F7 0%, #C7D7FA 50%, #EAD4F5 100%)",
        "gradient-sage": "linear-gradient(135deg, #D4EFDF 0%, #C8EAE4 50%, #FDF0C8 100%)",
        "gradient-blossom": "linear-gradient(135deg, #FDF0C8 0%, #F8CDDA 50%, #EAD4F5 100%)",
        // Multi-blob hero (diagonal + corner radial blend)
        "hero-wash":
          "radial-gradient(600px 480px at 20% 30%, rgba(255, 181, 167, 0.45) 0%, transparent 60%), radial-gradient(520px 420px at 80% 20%, rgba(224, 213, 247, 0.55) 0%, transparent 65%), radial-gradient(560px 420px at 90% 85%, rgba(253, 240, 200, 0.5) 0%, transparent 65%), radial-gradient(520px 420px at 10% 90%, rgba(199, 215, 250, 0.35) 0%, transparent 65%)",
        "auth-wash":
          "radial-gradient(500px 500px at -10% 40%, rgba(224, 213, 247, 0.7) 0%, transparent 60%), radial-gradient(400px 400px at 80% -10%, rgba(253, 240, 200, 0.7) 0%, transparent 65%), radial-gradient(400px 400px at -20% -10%, rgba(234, 212, 245, 0.6) 0%, transparent 65%), radial-gradient(500px 500px at 60% 90%, rgba(255, 181, 167, 0.35) 0%, transparent 60%)",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(45, 36, 56, 0.04), 0 8px 24px rgba(45, 36, 56, 0.06)",
        card: "0 1px 2px rgba(45, 36, 56, 0.04), 0 4px 16px rgba(45, 36, 56, 0.05)",
        "card-lg": "0 2px 8px rgba(45, 36, 56, 0.06), 0 20px 48px rgba(45, 36, 56, 0.08)",
      },
      borderRadius: {
        pill: "9999px",
        xl2: "20px",
        "2xl": "24px",
        "3xl": "28px",
      },
      maxWidth: {
        wrap: "1280px",
      },
    },
  },
  plugins: [],
};

export default config;
