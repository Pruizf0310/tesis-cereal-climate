import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        "bg-deep": "var(--bg-deep)",
        "bg-panel": "var(--bg-panel)",
        "bg-elev": "var(--bg-elev)",
        line: "var(--line)",
        "line-strong": "var(--line-strong)",
        ink: "var(--ink)",
        "ink-dim": "var(--ink-dim)",
        "ink-mute": "var(--ink-mute)",
        cool: "var(--accent-cool)",
        warm: "var(--accent-warm)",
        crop: "var(--accent-crop)",
        "risk-low": "var(--risk-low)",
        "risk-mod": "var(--risk-mod)",
        "risk-high": "var(--risk-high)",
        "risk-extr": "var(--risk-extr)",
        "enso-nina": "var(--enso-nina)",
        "enso-neut": "var(--enso-neut)",
        "enso-nino": "var(--enso-nino)"
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"]
      },
      letterSpacing: {
        tightest: "-0.04em",
        tighter: "-0.025em"
      },
      borderRadius: {
        xs: "2px",
        sm: "4px"
      },
      boxShadow: {
        glass: "0 1px 0 rgba(255,255,255,0.04) inset, 0 30px 90px rgba(0,0,0,0.45)"
      },
      backdropBlur: {
        xs: "6px"
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        }
      },
      animation: {
        "fade-up": "fade-up 320ms cubic-bezier(0.2, 0.7, 0.2, 1) both",
        shimmer: "shimmer 2.4s linear infinite"
      }
    }
  },
  plugins: []
};

export default config;
